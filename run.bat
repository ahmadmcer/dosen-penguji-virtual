@echo off
setlocal enabledelayedexpansion
title Dosen Penguji Virtual
echo ========================================================
echo Dosen Penguji Virtual - Auto Setup Launcher
echo ========================================================
echo.

:: 1. Cek apakah Python terinstal
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di sistem komputer Anda!
    echo Silakan unduh dan instal Python dari python.org terlebih dahulu,
    echo dan pastikan Anda mencentang "Add Python to PATH" saat instalasi.
    pause
    exit /b
)
echo [OK] Python terdeteksi.

:: 2. Cek/Buat Virtual Environment
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] Mengisolasi lingkungan ^(Virtual Environment^) belum ada. Membuat baru...
    python -m venv .venv
    echo [OK] Lingkungan isolasi berhasil dibuat di folder .venv.
)

:: 3. Aktifkan Virtual Environment
echo [INFO] Menyalakan Virtual Environment...
call .venv\Scripts\activate.bat

:: 4. Instal Dependensi
echo [INFO] Sinkronisasi pustaka ^(library^) yang dibutuhkan...
pip install -q -r requirements.txt --disable-pip-version-check
echo [OK] Semua pustaka siap.

:: 5. Cek file .env
if not exist ".env" (
    echo [WARNING] File .env tidak ditemukan!
    echo Membuat cetakan file .env untuk Anda...
    echo GEMINI_API_KEY=Ketik_API_Key_Anda_Disini > .env
    echo.
    echo ========================================================
    echo PERHATIAN PENTING!
    echo Saya telah membuat file bernama ".env" di folder ini.
    echo Tolong buka file tersebut dengan Notepad,
    echo lalu masukkan kunci API Gemini Anda.
    echo ========================================================
    pause
)

:: 6. Jalankan Streamlit
echo.
echo [INFO] Menyalakan server mesin...
streamlit run app.py
pause
