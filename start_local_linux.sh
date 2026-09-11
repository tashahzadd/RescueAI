#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -r requirements.txt
echo "RescueAI backend: http://127.0.0.1:8000"
echo "Swagger: http://127.0.0.1:8000/docs"
exec uvicorn main:app --host 127.0.0.1 --port 8000
