import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from config.prompts import EXAMINER_SYSTEM_PROMPT, EVALUATOR_SYSTEM_PROMPT, QUESTION_STAGES

class ChatEngine:
    def __init__(self, retriever):
        self.retriever = retriever
        
        # Inisialisasi LLM
        self.llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.3)
            
    def format_chat_history(self, messages):
        """Memformat riwayat obrolan dari Streamlit format ke string sederhana."""
        formatted = ""
        for msg in messages:
            role = "Mahasiswa" if msg["role"] == "user" else "Penguji"
            formatted += f"{role}: {msg['content']}\n\n"
        return formatted

    def generate_question(self, current_stage_index: int, chat_history: list):
        """Menghasilkan pertanyaan berdasarkan RAG dan stage saat ini."""
        stage_info = QUESTION_STAGES[current_stage_index]
        formatted_history = self.format_chat_history(chat_history)
        
        prompt = ChatPromptTemplate.from_template(EXAMINER_SYSTEM_PROMPT)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Buat RAG chain
        rag_chain = (
            {
                "context": itemgetter("fokus_pertanyaan") | self.retriever | format_docs,
                "nama_penguji": itemgetter("nama_penguji"),
                "persona": itemgetter("persona"),
                "tipe_pertanyaan": itemgetter("tipe_pertanyaan"),
                "fokus_pertanyaan": itemgetter("fokus_pertanyaan"),
                "chat_history": itemgetter("chat_history")
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Panggil LLM
        response = rag_chain.invoke({
            "nama_penguji": stage_info["nama_penguji"],
            "persona": stage_info["persona"],
            "tipe_pertanyaan": stage_info["tipe"],
            "fokus_pertanyaan": stage_info["fokus"],
            "chat_history": formatted_history
        })
        
        # Bersihkan format blok kode yang tidak disengaja dari AI
        response = response.replace("```markdown", "").replace("```text", "").replace("```", "")
        # Hapus indentasi berlebihan di awal baris yang menyebabkan markdown menganggapnya sebagai kode
        response = "\n".join(line.lstrip() if line.startswith("    ") or line.startswith("\t") else line for line in response.split("\n"))
        
        return response
        
    def generate_evaluation(self, chat_history: list):
        """Menghasilkan laporan evaluasi akhir."""
        formatted_history = self.format_chat_history(chat_history)
        prompt = ChatPromptTemplate.from_template(EVALUATOR_SYSTEM_PROMPT)
        
        chain = prompt | self.llm | StrOutputParser()
        
        response = chain.invoke({"chat_history": formatted_history})
        return response
