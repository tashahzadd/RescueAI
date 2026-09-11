#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, zipfile, os, json

PROJECT = Path("/content/app/rescueai")
BACKEND = PROJECT / "backend"
FRONTEND = PROJECT / "frontend"

if not PROJECT.exists():
    raise SystemExit(f"Project not found: {PROJECT}")
if not BACKEND.exists():
    raise SystemExit(f"Backend not found: {BACKEND}")
if not FRONTEND.exists():
    raise SystemExit(f"Frontend not found: {FRONTEND}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = PROJECT / f"_release_backup_{stamp}"
backup_dir.mkdir(exist_ok=True)

def backup(path):
    path = Path(path)
    if path.exists():
        rel = path.relative_to(PROJECT)
        dest = backup_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(path, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(path, dest)

def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("WROTE:", path.relative_to(PROJECT))

for rel in [
    "backend/requirements.txt", ".env.example", ".gitignore",
    "render.yaml", "Dockerfile", "docker-compose.yml",
    "start_local_windows.bat", "start_local_linux.sh", "DEPLOYMENT.md"
]:
    backup(PROJECT / rel)

write(BACKEND / "requirements.txt", '''fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
python-dotenv==1.0.1
python-multipart==0.0.9
psycopg2-binary==2.9.10
''')

write(PROJECT / ".env.example", '''DATABASE_URL=sqlite:///./rescueai.db
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
# Cloud example:
# DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
''')

write(PROJECT / ".gitignore", '''__pycache__/
*.py[cod]
.venv/
venv/
node_modules/
frontend/dist/
.env
*.pem
*.key
.vscode/
.idea/
.DS_Store
Thumbs.db
*.log
_release_backup_*/
*.db-shm
*.db-wal
''')

write(PROJECT / "render.yaml", '''services:
  - type: web
    name: rescueai-api
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/dashboard/stats
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.7
      - key: DATABASE_URL
        fromDatabase:
          name: rescueai-postgres
          property: connectionString

databases:
  - name: rescueai-postgres
    databaseName: rescueai
    user: rescueai
''')

write(PROJECT / "Dockerfile", '''FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/ /app/
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
''')

write(PROJECT / "docker-compose.yml", '''services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: rescueai
      POSTGRES_USER: rescueai
      POSTGRES_PASSWORD: rescueai_local_change_me
    volumes:
      - rescueai_postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+psycopg2://rescueai:rescueai_local_change_me@db:5432/rescueai
      PORT: 8000
    ports:
      - "8000:8000"

volumes:
  rescueai_postgres_data:
''')

write(PROJECT / "start_local_windows.bat", r'''@echo off
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
''')

write(PROJECT / "start_local_linux.sh", '''#!/usr/bin/env bash
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
''')
try:
    os.chmod(PROJECT / "start_local_linux.sh", 0o755)
except Exception:
    pass

write(BACKEND / "backup_database.py", '''from pathlib import Path
from datetime import datetime
import shutil

here = Path(__file__).resolve().parent
db = here / "rescueai.db"
if not db.exists():
    raise SystemExit(f"Database not found: {db}")

out = here / f"rescueai_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2(db, out)
print(out)
''')

write(BACKEND / "migrate_sqlite_to_postgres.py", '''import argparse
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.exc import IntegrityError

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sqlite", default="sqlite:///./rescueai.db")
    p.add_argument("--postgres", required=True)
    args = p.parse_args()

    src = create_engine(args.sqlite)
    dst = create_engine(args.postgres, pool_pre_ping=True)

    src_meta = MetaData()
    src_meta.reflect(bind=src)
    src_meta.create_all(bind=dst)

    dst_meta = MetaData()
    dst_meta.reflect(bind=dst)

    total_inserted = 0
    for s_table in src_meta.sorted_tables:
        name = s_table.name
        if name not in dst_meta.tables:
            print("SKIP:", name)
            continue

        d_table = dst_meta.tables[name]
        with src.connect() as conn:
            rows = [dict(r._mapping) for r in conn.execute(select(s_table))]

        inserted = 0
        for row in rows:
            try:
                with dst.begin() as conn:
                    conn.execute(d_table.insert().values(**row))
                inserted += 1
            except IntegrityError:
                pass

        total_inserted += inserted
        print(f"{name}: source={len(rows)} inserted={inserted}")

    print("Migration complete. Total inserted:", total_inserted)

if __name__ == "__main__":
    main()
''')

write(PROJECT / "DEPLOYMENT.md", '''# RescueAI Deployment

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
''')

manifest = {
    "generated_at": stamp,
    "destructive_reset_performed": False,
    "database_reseed_performed": False,
    "purpose": "GitHub, offline and permanent-cloud deployment support"
}
write(PROJECT / "release_manifest.json", json.dumps(manifest, indent=2))

out = Path("/content") / f"RescueAI_GitHub_Offline_{stamp}.zip"
skip = {".venv", "venv", "node_modules", "__pycache__", ".git"}

def skip_path(p):
    rel = p.relative_to(PROJECT)
    if any(part in skip for part in rel.parts):
        return True
    if any(part.startswith("_release_backup_") for part in rel.parts):
        return True
    if "frontend" in rel.parts and "dist" in rel.parts:
        return True
    if p.suffix in {".pyc", ".pyo"}:
        return True
    return False

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in PROJECT.rglob("*"):
        if p.is_file() and not skip_path(p):
            z.write(p, arcname=str(Path("rescueai") / p.relative_to(PROJECT)))

print("=" * 70)
print("RELEASE READY")
print("ZIP:", out)
print("Config backup:", backup_dir)
print("No database reset or reseed performed.")
print("=" * 70)
