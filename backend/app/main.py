import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .database import init_db
from .routers import documents, review, chat, dashboard

logger = logging.getLogger("veridoc")

app = FastAPI(title="VeriDoc API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    # Warm the embedding model once at startup rather than on the first
    # request, so the first upload isn't slowed down by a cold model load.
    # This is best-effort: if the model can't be downloaded (no network,
    # first run without internet access), the app still starts -- it just
    # logs a warning, and indexing will retry (and fail the same way)
    # per-document until the model becomes available.
    from .embeddings import embedding_model
    try:
        embedding_model.get_model()
        logger.info("Embedding model loaded and warm.")
    except Exception as exc:
        logger.warning("Embedding model could not be loaded at startup: %s", exc)

    from .llm.ollama_client import is_reachable
    from . import config
    if is_reachable():
        logger.info("Ollama reachable at %s", config.OLLAMA_URL)
    else:
        logger.warning(
            "Ollama not reachable at %s -- document extraction and Q&A will fail "
            "until it's running (`ollama serve`, `ollama pull %s`).",
            config.OLLAMA_URL, config.OLLAMA_MODEL,
        )


app.include_router(documents.router)
app.include_router(review.router)
app.include_router(chat.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="frontend")
