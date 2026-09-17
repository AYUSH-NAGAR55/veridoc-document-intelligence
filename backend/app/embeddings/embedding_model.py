"""Loads the Sentence-Transformers embedding model exactly once per
process and reuses it for every request — re-loading it per call was
flagged explicitly as a performance problem to avoid.

`get_model()` is called once at FastAPI startup (see main.py) so the
model is warm before the first upload arrives, and again lazily by
anything that imports this module directly (tests, scripts).
"""
import threading

from .. import config

_model = None
_lock = threading.Lock()
_load_error: Exception | None = None


def get_model():
    """Returns the loaded SentenceTransformer, loading it on first call.

    Raises the original exception (e.g. a network error reaching Hugging
    Face to download weights) on every call until it succeeds — callers
    should catch this and degrade gracefully rather than crash the whole
    pipeline.
    """
    global _model, _load_error
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        from sentence_transformers import SentenceTransformer
        try:
            _model = SentenceTransformer(config.EMBEDDING_MODEL)
        except Exception as exc:
            _load_error = exc
            raise
        return _model


def is_available() -> bool:
    try:
        get_model()
        return True
    except Exception:
        return False


def embed(texts: list[str]):
    """Returns a numpy array of shape (len(texts), dim), L2-normalized so
    inner-product search in FAISS is equivalent to cosine similarity.
    """
    import numpy as np
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors, dtype="float32")


def embedding_dim() -> int:
    model = get_model()
    return model.get_sentence_embedding_dimension()
