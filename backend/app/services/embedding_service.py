"""Selects between two embedding backends based on EMBEDDING_BACKEND:

- "lightweight" (default): a hashing vectorizer with no heavy dependencies.
  Safe on small/free hosting tiers (e.g. Render free 512MB).
- "sentence-transformers": a real neural embedding model. Higher retrieval
  quality, but requires the optional `sentence-transformers` package (which
  pulls in PyTorch) and meaningfully more memory - only enable this on a
  host with at least ~1GB RAM available to the backend process.

Either way the output dimensionality is fixed at 384 so the FAISS index
doesn't need to change based on backend.
"""
from functools import lru_cache

import numpy as np

from app.config import get_settings
from app.services.lightweight_embedding import embed_texts_lightweight, EMBEDDING_DIM  # noqa: F401


@lru_cache
def _get_st_model():
    # Imported lazily so the (optional, heavy) sentence-transformers/torch
    # dependency is never touched unless this backend is explicitly selected.
    from sentence_transformers import SentenceTransformer
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    settings = get_settings()
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")

    if settings.embedding_backend == "sentence-transformers":
        model = _get_st_model()
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype="float32")

    return embed_texts_lightweight(texts)


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]
