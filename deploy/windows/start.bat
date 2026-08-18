@echo off
echo Starting KyU Campus Connect...
cd /d "%~dp0"
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r backend\requirements.txt
) else (
    call venv\Scripts\activate.bat
)
cd backend
echo Starting server on http://localhost:8000
start "" http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000
