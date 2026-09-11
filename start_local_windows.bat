@echo off
setlocal
cd /d %~dp0backend
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
echo RescueAI backend: http://127.0.0.1:8000
echo Swagger: http://127.0.0.1:8000/docs
uvicorn main:app --host 127.0.0.1 --port 8000
