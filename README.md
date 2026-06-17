# Dosen Penguji Virtual 🎓

Sebuah aplikasi cerdas berbasis *Retrieval-Augmented Generation* (RAG) yang dirancang untuk membantu mahasiswa melakukan simulasi sidang skripsi. Aplikasi ini bertindak sebagai Dosen Penguji yang akan membaca naskah skripsi Anda dan memberikan pertanyaan kritis secara *real-time*.

## Fitur Unggulan

- **Pertanyaan Kontekstual & Akurat:** AI tidak berhalusinasi. Semua pertanyaan yang diajukan bersumber langsung dari metodologi, data, dan teks yang ada di dalam PDF Anda berkat implementasi RAG yang ketat.
- **Smart Auto-Retry:** Jangan khawatir jika skripsi Anda sangat tebal. Aplikasi ini memiliki sistem *Exponential Backoff* yang secara otomatis menjeda dan mengatur ulang antrean pengunggahan jika API menabrak limit (Rate Limit) dari Google Cloud.
- **Laporan Evaluasi:** Setelah 4 putaran tanya jawab, Dosen Penguji Virtual akan memberikan skor simulasi, membedah celah argumen Anda, dan memberikan saran perbaikan spesifik sebelum Anda maju ke sidang sungguhan.
- **Antarmuka Interaktif:** Dibangun dengan Streamlit, simulasi terasa seperti *chatting* sungguhan.

## Teknologi yang Digunakan

- **Frontend:** Streamlit
- **Orkestrasi AI:** LangChain
- **Vector Database:** Chroma (In-memory)
- **Model Embedding:** `models/gemini-embedding-2`
- **Model Bahasa (LLM):** `gemini-3.5-flash`

## Cara Instalasi & Penggunaan

1. **Kloning Repositori:**
   ```bash
   git clone <url-repo-anda>
   cd dosen-penguji-virtual
   ```

2. **Instalasi Dependensi:**
   Pastikan Anda menggunakan Python 3.9 atau lebih baru.
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurasi Lingkungan:**
   Ubah nama file `.env.example` menjadi `.env` lalu masukkan API Key Google Gemini Anda.
   ```env
   GEMINI_API_KEY=AIzaSyYourSecretKeyHere...
   ```

4. **Jalankan Aplikasi:**
   ```bash
   streamlit run app.py
   ```
   Aplikasi akan terbuka secara otomatis di *browser* Anda (biasanya di `http://localhost:8501`).

## Struktur Proyek

```text
/
├── .env                  # Variabel lingkungan rahasia (diabaikan oleh git)
├── requirements.txt      # Daftar pustaka Python
├── app.py                # Tampilan utama antarmuka Streamlit
├── core/                 
│   ├── rag_engine.py     # Logika ekstraksi PDF, Embedding, dan penanganan Rate Limit
│   └── chat_engine.py    # Logika rantai LLM (RAG Chain) untuk memproduksi tanya-jawab
├── config/               
│   └── prompts.py        # Kumpulan instruksi ketat (System Prompts) untuk kepribadian AI
└── docs/                 # Menyimpan log dan ide pengembangan
```

---
*Dibuat untuk membantu pejuang skripsi lulus dengan percaya diri!*
