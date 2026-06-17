# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-06-17

### Added
- Dukungan unggah format Microsoft Word (`.docx`) menggunakan `Docx2txtLoader` di menu *sidebar*.

## [1.1.0] - 2026-06-17

### Added
- **4 Persona Penguji:** Sistem *prompting* dinamis yang menghidupkan 4 gaya dosen (The Theorist, Detektif Metodologi, Pragmatis, dan The Sniper).
- **Mekanisme Follow-Up:** Batas simulasi diperpanjang menjadi 8 putaran (2 pertanyaan per penguji) yang mencakup pertanyaan utama dan serangan balik.
- **Indikator Identitas AI:** Menampilkan nama penguji (*prefix*) di antarmuka obrolan Streamlit agar terasa seperti berhadapan dengan panel dosen nyata.

## [1.0.0] - 2026-06-17

### Added
- **RAG Engine:** Implementasi `GoogleGenerativeAIEmbeddings` untuk membaca dokumen PDF Skripsi dan mengekstraknya menggunakan `Chroma`.
- **Chat Engine:** Implementasi model `gemini-3.5-flash` untuk memberikan pengalaman tanya jawab interaktif berbasis data naskah.
- **Anti Rate-Limit:** Mekanisme *Exponential Backoff* pintar untuk secara otomatis menangani pembatasan kuota (429) dan gangguan konektivitas (503, 504) dari server Google Cloud.
- **Progress Bar UI:** Indikator persentase visual yang memanjakan mata selama proses penyerapan dokumen berlangsung.
- **Laporan Evaluasi:** Skor akhir dan rekomendasi revisi setelah simulasi.

### Changed
- **Folder Restructuring:** Pembersihan struktur direktori. Semua *script* inti dipindahkan ke dalam folder `core/` dan `config/` agar memenuhi standar skalabilitas.
- **Model Migration:** Transisi dari model lokal yang lambat (Ollama) ke integrasi mutlak API Google Gemini yang sangat gesit.

### Removed
- Menghapus integrasi `langchain-ollama` dari _requirements_ dan menyembunyikan panel opsi model di antarmuka untuk mengurangi kebingungan pengguna.
