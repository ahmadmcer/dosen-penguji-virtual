import os
import time
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class RAGEngine:
    def __init__(self):
        # Inisialisasi model embedding
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY belum dikonfigurasi di file .env")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
        self.vectorstore = None

    def ingest_document(self, uploaded_file, progress_callback=None):
        """Mengekstrak teks dari file PDF atau DOCX yang diupload."""
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        file_content = uploaded_file.getvalue()
        
        # Hitung MD5 Hash untuk Caching
        import hashlib
        file_hash = hashlib.md5(file_content).hexdigest()
        db_path = f"./chroma_db/{file_hash}"
        complete_marker = f"{db_path}/ingestion_complete.txt"
        
        # Cek jika cache database sudah ada DAN prosesnya sudah 100% selesai (mencegah Race Condition multi-user)
        if os.path.exists(db_path) and os.path.exists(complete_marker):
            print(f"Loading from cache: {db_path}")
            self.vectorstore = Chroma(persist_directory=db_path, embedding_function=self.embeddings)
            return True, True # Beri sinyal is_cached = True
        
        # Simpan file sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        try:
            if file_extension == ".pdf":
                loader = PyPDFLoader(tmp_path)
            elif file_extension == ".docx":
                loader = Docx2txtLoader(tmp_path)
            else:
                raise ValueError(f"Format file {file_extension} tidak didukung.")
                
            pages = loader.load()
            
            # Memecah dokumen dengan chunk_size menengah agar pencarian semantik lebih tajam (akurat)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=300)
            splits = text_splitter.split_documents(pages)
            
            # Mencegah PDF bodong/scanned image lolos tanpa error
            if len(splits) == 0:
                raise ValueError("Dokumen ini tidak memiliki teks yang dapat dibaca (kemungkinan berupa PDF hasil scan/gambar). Harap gunakan PDF digital murni atau file DOCX.")
            
            import time
            # Membuat vectorstore dengan persist_directory
            self.vectorstore = Chroma(embedding_function=self.embeddings, persist_directory=db_path)
            batch_size = 5
            total_splits = len(splits)
            for i in range(0, total_splits, batch_size):
                if progress_callback:
                    progress_callback(i, total_splits)
                
                batch = splits[i:i+batch_size]
                success = False
                retries = 0
                while not success and retries < 10:
                    try:
                        self.vectorstore.add_documents(batch)
                        success = True
                        
                        if progress_callback:
                            progress_callback(min(i + batch_size, total_splits), total_splits)
                            
                        # Jeda 5.5 detik per 5 dokumen memastikan kita hanya mengirim ~54 request per menit
                        # (Mencegah terbentur strict limit 60 RPM dari GCP)
                        if i + batch_size < total_splits:
                            time.sleep(5.5)
                    except Exception as e:
                        error_msg = str(e)
                        # Retry jika terkena limit atau masalah koneksi server (503/502/504)
                        retry_keywords = ["429", "RESOURCE_EXHAUSTED", "Quota exceeded", "503", "UNAVAILABLE", "502", "504", "connection"]
                        if any(keyword in error_msg for keyword in retry_keywords):
                            retries += 1
                            print(f"Hit network/API limit. Retrying batch {i} in {5 * retries} seconds...")
                            time.sleep(5 * retries) # Jeda makin lama jika terus diblokir
                        else:
                            raise e
                    
            # Buat penanda bahwa proses telah 100% selesai
            if not os.path.exists(db_path):
                os.makedirs(db_path)
            with open(complete_marker, "w") as f:
                f.write("done")
                
            return True, False # is_cached = False
        except Exception as e:
            print(f"Error saat ingest dokumen: {e}")
            # Lakukan ROLLBACK: Bersihkan folder yang setengah jadi agar tidak menyebabkan duplikasi vektor
            import shutil
            if os.path.exists(db_path):
                shutil.rmtree(db_path, ignore_errors=True)
            return False, False
        finally:
            # Hapus file sementara
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    def get_retriever(self):
        """Mengembalikan retriever object untuk LangChain."""
        if self.vectorstore is None:
            return None
        return self.vectorstore.as_retriever(search_kwargs={"k": 3})
