"""FAISS-backed vector index for the whole app (one shared index across
all documents, filtered by document_id at query/delete time).

Uses IndexIDMap over a flat inner-product index (cosine similarity,
since embeddings are L2-normalized) specifically because IndexIDMap is
one of the few FAISS index types that supports true removal — deleting
a document must not leave stale vectors behind (an explicit requirement:
no orphaned index entries after deletion).

A parallel `metadata` dict keeps vector_id -> {chunk_id, document_id,
location, text} so a FAISS hit can be traced all the way back to its
source. Persisted to disk as JSON alongside the FAISS index file so both
survive a restart.
"""
import json
import os
import threading

import numpy as np

from .. import config

_INDEX_PATH = os.path.join(config.FAISS_INDEX_DIR, "index.faiss")
_META_PATH = os.path.join(config.FAISS_INDEX_DIR, "metadata.json")

_lock = threading.Lock()
_index = None
_metadata: dict[int, dict] = {}
_next_id = 1


def _ensure_loaded(dim: int):
    global _index, _metadata, _next_id
    if _index is not None:
        return
    import faiss
    if os.path.exists(_INDEX_PATH) and os.path.exists(_META_PATH):
        _index = faiss.read_index(_INDEX_PATH)
        with open(_META_PATH) as f:
            raw = json.load(f)
        _metadata = {int(k): v for k, v in raw.items()}
        _next_id = (max(_metadata.keys()) + 1) if _metadata else 1
    else:
        _index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))


def _persist():
    import faiss
    faiss.write_index(_index, _INDEX_PATH)
    with open(_META_PATH, "w") as f:
        json.dump(_metadata, f)


def add_batch(document_id: str, items: list[dict]):
    """items: list of {chunk_id, vector, location, text}"""
    global _next_id
    if not items:
        return
    with _lock:
        _ensure_loaded(dim=len(items[0]["vector"]))
        ids = list(range(_next_id, _next_id + len(items)))
        _next_id += len(items)
        vectors = np.array([it["vector"] for it in items], dtype="float32")
        _index.add_with_ids(vectors, np.array(ids))
        for vec_id, it in zip(ids, items):
            _metadata[vec_id] = {
                "chunk_id": it["chunk_id"], "document_id": document_id,
                "location": it["location"], "text": it["text"],
            }
        _persist()


def search(query_vector: np.ndarray, k: int = 6, document_id: str | None = None) -> list[dict]:
    with _lock:
        if _index is None or _index.ntotal == 0:
            return []
        fetch_k = k * 5 if document_id else k
        scores, ids = _index.search(np.array([query_vector], dtype="float32"), min(fetch_k, _index.ntotal))
        results = []
        for score, vec_id in zip(scores[0], ids[0]):
            if vec_id == -1:
                continue
            meta = _metadata.get(int(vec_id))
            if not meta:
                continue
            if document_id and meta["document_id"] != document_id:
                continue
            results.append({**meta, "score": float(score)})
            if len(results) >= k:
                break
        return results


def remove_document(document_id: str):
    """Removes every vector belonging to a document — the one operation
    FAISS's IndexIDMap actually supports natively (remove_ids), which is
    exactly why IndexIDMap was chosen over a plain flat index.
    """
    with _lock:
        if _index is None:
            return
        ids_to_remove = [vec_id for vec_id, meta in _metadata.items() if meta["document_id"] == document_id]
        if not ids_to_remove:
            return
        _index.remove_ids(np.array(ids_to_remove, dtype="int64"))
        for vec_id in ids_to_remove:
            _metadata.pop(vec_id, None)
        _persist()


def total_vectors() -> int:
    return 0 if _index is None else _index.ntotal
