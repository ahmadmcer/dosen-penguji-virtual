import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.prompts import DYNAMIC_EXAMINER_PROMPT, EVALUATOR_SYSTEM_PROMPT

class ChatEngine:
    def __init__(self, retriever):
        self.retriever = retriever
        
        # Inisialisasi LLM
        self.llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3)
            
    def format_chat_history(self, messages, limit_memory=True):
        """Memformat riwayat obrolan dari Streamlit format ke string sederhana."""
        formatted = ""
        # Jendela Memori: Hanya ambil 12 pesan terakhir (6 giliran interaksi) 
        # untuk mencegah kelebihan token (Token Bloat) dan mempercepat respons AI.
        recent_messages = messages[-12:] if (limit_memory and len(messages) > 12) else messages
        
        import re
        for msg in recent_messages:
            role = "Mahasiswa" if msg["role"] == "user" else "Penguji"
            # Menggunakan regex untuk membersihkan [SELESAI] beserta bintang (**) dan titik
            clean_content = re.sub(r"\**\[SELESAI\]\**\.?", "", msg['content']).strip()
            formatted += f"{role}: {clean_content}\n\n"
        return formatted

    def generate_question(self, chat_history: list):
        """Menghasilkan pertanyaan secara dinamis berdasarkan RAG dan percakapan terakhir."""
        formatted_history = self.format_chat_history(chat_history)
        
        prompt = ChatPromptTemplate.from_template(DYNAMIC_EXAMINER_PROMPT)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Cari konteks berdasarkan jawaban terakhir mahasiswa
        # Jika belum ada percakapan (pertanyaan pertama), cari kata kunci umum skripsi
        search_query = "Latar belakang, rumusan masalah, metodologi penelitian, dan kesimpulan utama"
        if len(chat_history) > 0:
            last_user_msg = ""
            last_ai_msg = ""
            # Cari pesan terakhir user dan AI
            for msg in reversed(chat_history):
                if msg["role"] == "user" and not last_user_msg:
                    last_user_msg = msg["content"]
                elif msg["role"] == "assistant" and not last_ai_msg:
                    # Ambil murni pertanyaan AI saja
                    last_ai_msg = msg["content"].replace("**[Panel Penguji]**\n\n", "")
                if last_user_msg and last_ai_msg:
                    break
            
            if last_user_msg:
                # Pencarian Cerdas (Smart Fallback): Jika jawaban mahasiswa sangat pendek (< 10 kata),
                # gabungkan pertanyaan AI sebelumnya dengan jawaban mahasiswa untuk RAG query
                if len(last_user_msg.split()) < 10 and last_ai_msg:
                    search_query = f"Pertanyaan: {last_ai_msg}\nJawaban: {last_user_msg}"
                else:
                    search_query = last_user_msg

        # Tarik dokumen relevan dari ChromaDB
        docs = self.retriever.invoke(search_query)
        context_str = format_docs(docs)
        
        # Panggil LLM
        chain = prompt | self.llm | StrOutputParser()
        # Injeksi Constraint-Aware Pacing (Indikator Putaran Sidang)
        # Menghitung jumlah putaran (1 Q&A = 1 putaran, maka len/2)
        current_turn = (len(chat_history) // 2) + 1
        max_turns = 10
        
        pacing_instruction = f"\n\n[INFO SISTEM]: Saat ini Anda berada pada putaran pertanyaan ke-{current_turn} dari maksimal {max_turns} putaran sidang.\n"
        
        if current_turn < max_turns - 2:
            pacing_instruction += "INSTRUKSI: Fokuslah menggali satu topik spesifik (teori/metode/hasil) secara mendalam dan tajam."
        elif current_turn < max_turns:
            pacing_instruction += "INSTRUKSI: Waktu sidang segera habis! Segera beralih ke celah kelemahan fatal atau poin krusial lain yang belum sempat Anda tanyakan."
        else:
            pacing_instruction += "INSTRUKSI DARURAT: INI ADALAH GILIRAN TERAKHIR ANDA! Rumuskan satu pertanyaan pamungkas yang sangat komprehensif untuk merangkum seluruh keraguan Anda yang tersisa. Anda WAJIB mengakhiri kalimat penutup Anda dengan kode `[SELESAI]`."
            
        # Panggil LLM dengan konteks, riwayat obrolan, dan suntikan pacing kesadaran waktu
        response = chain.invoke({
            "context": context_str,
            "chat_history": formatted_history + pacing_instruction
        })
        
        # Bersihkan format blok kode yang tidak disengaja dari AI
        response = response.replace("```markdown", "").replace("```text", "").replace("```", "")
        response = "\n".join(line.lstrip() if line.startswith("    ") or line.startswith("\t") else line for line in response.split("\n"))
        
        # Deteksi apakah AI mengeluarkan bendera SELESAI
        import re
        is_finished = False
        if "[SELESAI]" in response:
            is_finished = True
            response = re.sub(r"\**\[SELESAI\]\**\.?", "", response).strip()
            
        return response, is_finished
        
    def generate_evaluation(self, chat_history: list):
        """Menghasilkan laporan evaluasi akhir."""
        # BUG FIXED: Jangan limit memory saat merumuskan evaluasi akhir agar nilainya adil!
        formatted_history = self.format_chat_history(chat_history, limit_memory=False)
        prompt = ChatPromptTemplate.from_template(EVALUATOR_SYSTEM_PROMPT)
        
        chain = prompt | self.llm | StrOutputParser()
        
        response = chain.invoke({"chat_history": formatted_history})
        return response
