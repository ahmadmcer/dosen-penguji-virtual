# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-06-17

### Added
- **RAG Engine:** Implementasi `GoogleGenerativeAIEmbeddings` untuk membaca dokumen PDF Skripsi dan mengubahnya ke dalam format vektor menggunakan `Chroma`.
- **Chat Engine:** Implementasi model `gemini-3.5-flash` untuk memberikan pengalaman tanya jawab interaktif *real-time* berbasis data PDF.
- **Auto-Retry & Rate Limiting:** Mekanisme Exponential Backoff pintar di dalam `rag_engine.py` untuk secara otomatis mengatasi pembatasan kuota (*Rate Limit* 429) dan gangguan konektivitas (503, 504) dari server Google Cloud.
- **Progress Bar UI:** Penambahan indikator pemuatan visual di antarmuka Streamlit selama proses pengunggahan dokumen.
- **Sanitasi Output Markdown:** Filter keamanan pada teks *output* AI untuk mencegah terbentukknya blok kode yang tidak sengaja ter-render oleh antarmuka Streamlit.

### Changed
- **Folder Restructuring:** Refaktorisasi besar pada arsitektur proyek, memisahkan modul ke dalam folder `core/`, `config/`, `docs/`, dan `tests/` agar lebih terukur (scalable).
- **Model Migration:** Transisi penuh dari model Ollama Lokal ke Gemini API (Tier 1) untuk performa *reasoning* yang jauh lebih cepat dan andal.

### Removed
- Integrasi *library* `langchain-ollama` dan parameter pengaturan UI untuk model pihak ketiga telah sepenuhnya dihapus guna memfokuskan aplikasi pada ekosistem Google Gemini.
