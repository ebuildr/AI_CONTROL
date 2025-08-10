@echo off
echo Starting AI Control System...
cd /d "C:\Users\ebuil\GPT-OSS\AI_CONTROL"
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
echo Virtual environment activated
echo Starting server on http://localhost:8002
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
pause
