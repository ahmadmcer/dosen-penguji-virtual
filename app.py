import streamlit as st
import os
from dotenv import load_dotenv
from core.rag_engine import RAGEngine
from core.chat_engine import ChatEngine

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Dosen Penguji Virtual", page_icon="🎓", layout="wide")

st.title("🎓 Dosen Penguji Virtual")
st.markdown("Unggah PDF Skripsi Anda dan mulai simulasi sidang dinamis dengan Panel Dosen Penguji.")

# Inisialisasi state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_finished" not in st.session_state:
    st.session_state.is_finished = False
if "document_processed" not in st.session_state:
    st.session_state.document_processed = False
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = None

# Sidebar
with st.sidebar:
    st.header("📄 Unggah Skripsi")
    uploaded_file = st.file_uploader("Pilih file Skripsi (PDF/DOCX)", type=["pdf", "docx"])
    
    if st.button("Mulai Pemrosesan"):
        if uploaded_file is not None:
            with st.spinner("Membaca dan memproses dokumen..."):
                try:
                    rag = RAGEngine()
                    
                    progress_bar = st.progress(0, text="Menyiapkan dokumen...")
                    def update_progress(current, total):
                        pct = int((current / total) * 100) if total > 0 else 0
                        progress_bar.progress(min(current / total, 1.0), text=f"Memproses {current} dari {total} bagian ({pct}%)")
                        
                    success, is_cached = rag.ingest_document(uploaded_file, progress_callback=update_progress)
                    if success:
                        progress_bar.empty()
                        st.session_state.rag_engine = rag
                        st.session_state.document_processed = True
                        st.session_state.messages = [] # Reset chat
                        st.session_state.is_finished = False
                        
                        # Bersihkan engine lama jika pengguna mengunggah dokumen baru
                        if "chat_engine" in st.session_state:
                            del st.session_state.chat_engine
                        
                        if is_cached:
                            st.success("⚡ Dokumen dimuat secara instan dari memori cache! Simulasi dimulai.")
                        else:
                            st.success("Dokumen siap! Simulasi dimulai.")
                        st.rerun()
                    else:
                        st.error("Gagal memproses dokumen.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Silakan unggah dokumen PDF atau DOCX terlebih dahulu.")

    # Tombol Akhiri Sesi Paksa
    if st.session_state.document_processed and not st.session_state.is_finished:
        st.markdown("---")
        if st.button("🛑 Akhiri Sidang Paksa"):
            st.session_state.is_finished = True
            st.rerun()

# Main area chat
if st.session_state.document_processed:
    # Menggunakan pola Singleton: Mencegah instansiasi klien LLM Google berulang kali pada tiap refresh UI
    if "chat_engine" not in st.session_state:
        try:
            st.session_state.chat_engine = ChatEngine(st.session_state.rag_engine.get_retriever())
        except Exception as e:
            st.error(f"Gagal menginisialisasi engine LLM: {str(e)}")
            st.stop()
            
    chat_engine = st.session_state.chat_engine
    
    # Generate pertanyaan pertama jika kosong
    if len(st.session_state.messages) == 0 and not st.session_state.is_finished:
        with st.spinner("Panel Dosen sedang menyiapkan pertanyaan pertama..."):
            try:
                first_q, _ = chat_engine.generate_question([])
                st.session_state.messages.append({"role": "assistant", "content": f"**[Panel Penguji]**\n\n{first_q}"})
                st.rerun()
            except Exception as e:
                st.error(f"Error saat membuat pertanyaan: {str(e)}")

    # Tampilkan chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Logika interaksi user
    if not st.session_state.is_finished:
        # Cegah "Ghost Input": Jangan tampilkan kolom ketik jika AI gagal memberi pertanyaan pertama
        is_ready_for_input = len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "assistant"
        
        if is_ready_for_input:
            if prompt := st.chat_input("Ketik jawaban Anda di sini..."):
                # Tambahkan jawaban user
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
            
                # Blok AI generate harus berada DI DALAM blok "if prompt:" agar AI hanya menjawab setelah user mengetik
                with st.chat_message("assistant"):
                    with st.spinner("Dosen menelaah jawaban Anda..."):
                        try:
                            next_q, ai_finished = chat_engine.generate_question(st.session_state.messages)
                            
                            # Tambahkan ke UI
                            st.session_state.messages.append({"role": "assistant", "content": f"**[Panel Penguji]**\n\n{next_q}"})
                            
                            if ai_finished:
                                st.session_state.is_finished = True
                                st.info("Panel Penguji telah menyudahi sesi tanya jawab. Sedang merumuskan evaluasi...")
                                # Generate Evaluasi seketika
                                eval_report = chat_engine.generate_evaluation(st.session_state.messages)
                                st.session_state.messages.append({"role": "assistant", "content": f"**[Ketua Sidang / Evaluasi Akhir]**\n\n{eval_report}"})
                                st.rerun()
                            else:
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error saat membuat pertanyaan: {str(e)}")

    else:
        # Jika ditekan paksa (AI belum finish, tapi evaluate belum digenerate)
        has_eval = any("**[Ketua Sidang / Evaluasi Akhir]**" in m["content"] for m in st.session_state.messages)
        
        if not has_eval:
            with st.spinner("Menyusun laporan evaluasi akhir..."):
                try:
                    eval_report = chat_engine.generate_evaluation(st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": f"**[Ketua Sidang / Evaluasi Akhir]**\n\n{eval_report}"})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saat menyusun evaluasi: {str(e)}")
                    
        st.success("Simulasi sidang telah selesai sepenuhnya. Anda dapat me-refresh halaman atau mengunggah dokumen baru untuk mengulang.")
else:
    st.info("Silakan unggah dokumen PDF atau DOCX di sidebar sebelah kiri dan klik 'Mulai Pemrosesan'.")
