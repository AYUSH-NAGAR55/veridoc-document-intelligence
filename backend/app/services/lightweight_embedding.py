"""A dependency-light embedding method: a hashing vectorizer over word tokens,
L2-normalized so cosine/inner-product search behaves sensibly. This exists so
VeriDoc can run comfortably on small hosts (e.g. Render's free 512MB tier)
without pulling in PyTorch, which sentence-transformers requires and which can
exceed memory limits on constrained instances.

It's less semantically aware than a real embedding model - it matches on
shared vocabulary rather than meaning - but it's real, deterministic, and
fast, and pairs reasonably with the mock LLM provider's own keyword-overlap
answering. Swap to EMBEDDING_BACKEND=sentence-transformers on a host with
enough RAM (roughly 1GB+) for higher-quality retrieval.
"""
import hashlib
import re

import numpy as np

EMBEDDING_DIM = 384
_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


def _hash_index(token: str) -> int:
    digest = hashlib.md5(token.lower().encode("utf-8")).hexdigest()
    return int(digest, 16) % EMBEDDING_DIM


def _vectorize(text: str) -> np.ndarray:
    vec = np.zeros(EMBEDDING_DIM, dtype="float32")
    for token in _TOKEN_RE.findall(text or ""):
        vec[_hash_index(token)] += 1.0
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec /= norm
    return vec


def embed_texts_lightweight(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")
    return np.stack([_vectorize(t) for t in texts]).astype("float32")
