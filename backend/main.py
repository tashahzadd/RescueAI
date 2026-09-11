import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from database import Base, engine
import models
from routers import incidents, misc, demo, auth_routes


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rescueai")


# ---------------------------------------------------------------------------
# Safe database migration
# ---------------------------------------------------------------------------

def ensure_auth_columns():
    """
    Safely upgrade the existing users table for authentication.

    This does NOT delete, reset, reseed, or modify existing RescueAI data.
    It only adds missing columns.
    """

    try:
        with engine.begin() as connection:

            # PostgreSQL
            if engine.dialect.name == "postgresql":

                connection.execute(
                    text(
                        """
                        ALTER TABLE users
                        ADD COLUMN IF NOT EXISTS password_hash VARCHAR;
                        """
                    )
                )

                connection.execute(
                    text(
                        """
                        ALTER TABLE users
                        ADD COLUMN IF NOT EXISTS is_active BOOLEAN
                        NOT NULL DEFAULT TRUE;
                        """
                    )
                )

            # SQLite development fallback
            elif engine.dialect.name == "sqlite":

                columns = connection.execute(
                    text("PRAGMA table_info(users)")
                ).fetchall()

                existing_columns = {
                    column[1] for column in columns
                }

                if "password_hash" not in existing_columns:
                    connection.execute(
                        text(
                            """
                            ALTER TABLE users
                            ADD COLUMN password_hash VARCHAR;
                            """
                        )
                    )

                if "is_active" not in existing_columns:
                    connection.execute(
                        text(
                            """
                            ALTER TABLE users
                            ADD COLUMN is_active BOOLEAN
                            NOT NULL DEFAULT 1;
                            """
                        )
                    )

        logger.info(
            "Authentication database columns verified successfully."
        )

    except Exception:
        logger.exception(
            "Unable to verify authentication database columns."
        )
        raise


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RescueAI",
    description=(
        "AI Emergency Response & Resource Coordination System - "
        "a decision-support platform. The AI NEVER autonomously "
        "dispatches real resources; every recommendation requires "
        "human approval. All data in this deployment is synthetic/demo data."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

Base.metadata.create_all(bind=engine)

ensure_auth_columns()


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(incidents.router)

app.include_router(misc.resources_router)

app.include_router(misc.hospitals_router)

app.include_router(misc.dashboard_router)

app.include_router(misc.audit_router)

app.include_router(misc.notifications_router)

app.include_router(demo.router)


# ---------------------------------------------------------------------------
# API information
# ---------------------------------------------------------------------------

@app.get("/api")
def api_root():
    return {
        "service": "RescueAI",
        "status": (
            "operational "
            "(decision-support only - no real dispatch capability)"
        ),
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }


# ---------------------------------------------------------------------------
# Optional built frontend
# ---------------------------------------------------------------------------

STATIC_FRONTEND_DIR = os.path.join(
    os.path.dirname(__file__),
    "static_frontend",
)

if os.path.isdir(STATIC_FRONTEND_DIR):

    app.mount(
        "/",
        StaticFiles(
            directory=STATIC_FRONTEND_DIR,
            html=True,
        ),
        name="frontend",
    )

    logger.info(
        "Serving built frontend from %s",
        STATIC_FRONTEND_DIR,
    )

else:

    @app.get("/")
    def root():
        return {
            "service": "RescueAI (backend-only mode)",
            "note": (
                "No built frontend found at ./static_frontend - "
                "API is available under /api and /docs."
            ),
        }
