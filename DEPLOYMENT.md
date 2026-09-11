# RescueAI Deployment

## Offline Windows
Double-click `start_local_windows.bat`.

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

## Offline Linux
```bash
chmod +x start_local_linux.sh
./start_local_linux.sh
```

## Local PostgreSQL with Docker
```bash
docker compose up --build -d
```

## Permanent cloud architecture
Hugging Face Static Frontend -> Permanent FastAPI Backend -> Persistent PostgreSQL

Do not rely on cloud-local SQLite for production persistence.

## Backup current SQLite
```bash
cd backend
python backup_database.py
```

## Migrate SQLite to PostgreSQL
```bash
python migrate_sqlite_to_postgres.py --sqlite sqlite:///./rescueai.db --postgres "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DB"
```

## Frontend
Replace the old ngrok API base with the permanent backend URL.

Recommended Vite pattern:
```js
const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
```

Set production:
```text
VITE_API_BASE_URL=https://YOUR-PERMANENT-BACKEND/api
```

## GitHub
Do not commit `.env`, ngrok tokens, database passwords or API secrets.
