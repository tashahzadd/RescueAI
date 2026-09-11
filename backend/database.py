"""
Database configuration.

Defaults to a local SQLite file so the hackathon MVP runs with zero setup.
Set DATABASE_URL in .env to point at PostgreSQL for a "real" deployment,
e.g. postgresql+psycopg2://user:pass@localhost:5432/rescueai
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rescueai.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
