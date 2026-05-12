from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api import datasets, executions, logs, proposals
from backend.app.core.env import load_local_env
from backend.app.core.paths import RUNS_DIR, ensure_runtime_dirs
from backend.app.db.storage import init_db
from backend.app.services.dataset_service import ensure_sample_data

ensure_runtime_dirs()


def _cors_origins() -> list[str]:
    load_local_env()
    raw = os.getenv("BACKEND_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_runtime_dirs()
    ensure_sample_data()
    init_db()
    yield


app = FastAPI(title="AI Analysis Workbench API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/artifacts", StaticFiles(directory=RUNS_DIR), name="artifacts")

app.include_router(datasets.router)
app.include_router(proposals.router)
app.include_router(executions.router)
app.include_router(logs.router)
