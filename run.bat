@echo off
:: ============================================================
:: run.bat — One-click launcher for DocuMind RAG System
:: ============================================================

:: CRITICAL: Change to the folder where THIS .bat file lives.
:: %~dp0 = the directory of the .bat file (e.g. C:\Users\bhave\Desktop\dox\)
:: Without this, double-clicking opens from a random working directory.
cd /d "%~dp0"

echo.
echo  =========================================
echo    DocuMind RAG System - Starting Up...
echo  =========================================
echo.

:: ── Check .env exists ─────────────────────────────────────────────────────────
if not exist ".env" (
    echo  [ERROR] .env file not found!
    echo  Please open .env and add your GROQ_API_KEY.
    echo  Get a free key at: https://console.groq.com
    pause
    exit /b 1
)

:: ── Check venv was created ────────────────────────────────────────────────────
if not exist ".venv\Scripts\uvicorn.exe" (
    echo  [ERROR] Virtual environment not found!
    echo  Please run this in your terminal first:
    echo.
    echo     C:\Users\bhave\.local\bin\uv.exe venv .venv --python 3.11
    echo     C:\Users\bhave\.local\bin\uv.exe pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

:: ── Start FastAPI backend ──────────────────────────────────────────────────────
:: We use the FULL PATH to uvicorn.exe inside the venv — no activation needed!
echo  [1/2] Starting FastAPI backend on http://localhost:8000 ...
start "DocuMind-API" cmd /k "cd /d "%~dp0" && .venv\Scripts\uvicorn.exe app.main:app --reload --port 8000"

:: Wait 4 seconds for FastAPI to be ready before Streamlit tries to connect
timeout /t 4 /nobreak >nul

:: ── Start Streamlit UI ─────────────────────────────────────────────────────────
echo  [2/2] Starting Streamlit UI on http://localhost:8501 ...
start "DocuMind-UI" cmd /k "cd /d "%~dp0" && .venv\Scripts\streamlit.exe run streamlit_app.py --server.port 8501"

echo.
echo  =========================================
echo    Both servers are starting!
echo.
echo    API Docs : http://localhost:8000/docs
echo    App UI   : http://localhost:8501
echo  =========================================
echo.
echo  Two terminal windows should have opened.
echo  Keep them running. Close them to stop.
echo.
pause
