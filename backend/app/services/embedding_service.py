"""Loads the sentence-transformers embedding model exactly once per process
and reuses it for every request - re-loading it per call is a common and
costly performance mistake."""
from functools import lru_cache

import numpy as np

from app.config import get_settings


@lru_cache
def _get_model():
    from sentence_transformers import SentenceTransformer
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype="float32")
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors, dtype="float32")


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]
