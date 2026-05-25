"""
main.py — FastAPI application entry point.

Startup:
  1. Load .env
  2. Index documents into vector store
  3. Mount static frontend
  4. Register API routes
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.services.indexer import index_documents

# ── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── app ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="RAG Chat Assistant",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    docs_path = os.getenv("DOCS_PATH", "docs.json")
    index_documents(docs_path)
    logger.info("Application ready.")

# ── health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy"}

# ── api routes ────────────────────────────────────────────────────────────────
app.include_router(chat_router, prefix="/api")

# ── frontend ──────────────────────────────────────────────────────────────────
frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))
