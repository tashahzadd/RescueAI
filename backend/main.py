import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import Base, engine
import models  # noqa: F401 - ensures models are registered before create_all
from routers import incidents, misc, demo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rescueai")

app = FastAPI(
    title="RescueAI",
    description=(
        "AI Emergency Response & Resource Coordination System - a decision-support "
        "platform. The AI NEVER autonomously dispatches real resources; every "
        "recommendation requires human approval. All data in this deployment is "
        "synthetic/demo data."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# All API routes live under /api/... so that, in combined-deployment mode
# (see below), they never collide with the frontend's static asset paths.
app.include_router(incidents.router)
app.include_router(misc.resources_router)
app.include_router(misc.hospitals_router)
app.include_router(misc.dashboard_router)
app.include_router(misc.audit_router)
app.include_router(misc.notifications_router)
app.include_router(demo.router)


@app.get("/api")
def api_root():
    return {
        "service": "RescueAI",
        "status": "operational (decision-support only - no real dispatch capability)",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Combined-deployment mode: if a built frontend (frontend/dist, copied here
# as ./static_frontend by the root Dockerfile) is present, serve it too, so
# a single container/Space can host both the API and the UI. When running
# the backend standalone (e.g. `uvicorn main:app` during local dev, or in a
# Colab cell), this directory won't exist and the API behaves exactly as a
# standalone service - nothing else changes.
# ---------------------------------------------------------------------------
STATIC_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "static_frontend")
if os.path.isdir(STATIC_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=STATIC_FRONTEND_DIR, html=True), name="frontend")
    logger.info("Serving built frontend from %s", STATIC_FRONTEND_DIR)
else:
    @app.get("/")
    def root():
        return {
            "service": "RescueAI (backend-only mode)",
            "note": "No built frontend found at ./static_frontend - API is available under /api and /docs.",
        }
