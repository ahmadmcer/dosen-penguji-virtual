import streamlit as st
import os
from dotenv import load_dotenv
from core.rag_engine import RAGEngine
from core.chat_engine import ChatEngine
from config.prompts import QUESTION_STAGES

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Dosen Penguji Virtual", page_icon="🎓", layout="wide")

st.title("🎓 Dosen Penguji Virtual")
st.markdown("Unggah PDF Skripsi Anda dan mulai simulasi sidang dengan AI Dosen Penguji.")

# Inisialisasi state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_stage" not in st.session_state:
    st.session_state.current_stage = 0
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
                        st.session_state.current_stage = 0
                        st.session_state.is_finished = False
                        
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

# Main area chat
if st.session_state.document_processed:
    # Init ChatEngine
    try:
        chat_engine = ChatEngine(st.session_state.rag_engine.get_retriever())
    except Exception as e:
        st.error(f"Gagal menginisialisasi engine LLM: {str(e)}")
        st.stop()
    
    # Generate pertanyaan pertama jika kosong
    if len(st.session_state.messages) == 0 and not st.session_state.is_finished:
        with st.spinner("AI sedang menyiapkan pertanyaan pertama..."):
            try:
                first_q = chat_engine.generate_question(st.session_state.current_stage, [])
                nama_penguji = QUESTION_STAGES[st.session_state.current_stage]["nama_penguji"]
                st.session_state.messages.append({"role": "assistant", "content": f"**[{nama_penguji}]**\n\n{first_q}"})
                st.rerun()
            except Exception as e:
                st.error(f"Error saat membuat pertanyaan: {str(e)}")

    # Tampilkan chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Logika interaksi user
    if not st.session_state.is_finished:
        if prompt := st.chat_input("Ketik jawaban Anda di sini..."):
            # Tambahkan jawaban user
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Naikkan stage pertanyaan
            st.session_state.current_stage += 1
            
            with st.chat_message("assistant"):
                if st.session_state.current_stage < len(QUESTION_STAGES):
                    # Lanjut pertanyaan berikutnya
                    with st.spinner("Menganalisis jawaban dan menyiapkan pertanyaan..."):
                        try:
                            next_q = chat_engine.generate_question(st.session_state.current_stage, st.session_state.messages)
                            nama_penguji = QUESTION_STAGES[st.session_state.current_stage]["nama_penguji"]
                            st.session_state.messages.append({"role": "assistant", "content": f"**[{nama_penguji}]**\n\n{next_q}"})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saat membuat pertanyaan: {str(e)}")
                else:
                    # Sudah 4 pertanyaan, masuk ke fase evaluasi
                    st.session_state.is_finished = True
                    with st.spinner("Menyusun laporan evaluasi..."):
                        try:
                            eval_report = chat_engine.generate_evaluation(st.session_state.messages)
                            st.session_state.messages.append({"role": "assistant", "content": f"**[Ketua Sidang / Pembimbing]**\n\n{eval_report}"})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saat menyusun evaluasi: {str(e)}")

    else:
        st.info("Simulasi sidang telah selesai. Anda dapat me-refresh halaman atau mengunggah dokumen baru untuk mengulang.")
else:
    st.info("Silakan unggah dokumen PDF atau DOCX di sidebar sebelah kiri dan klik 'Mulai Pemrosesan'.")
