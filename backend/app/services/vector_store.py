"""A small persistent wrapper around a single global FAISS index. Keeps
vector -> chunk -> document -> source location traceable via a JSON sidecar
file, since FAISS itself only stores vectors and integer ids."""
import json
import os
import threading

import faiss
import numpy as np

from app.config import get_settings

_lock = threading.Lock()
_settings = get_settings()

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class VectorStore:
    def __init__(self):
        os.makedirs(_settings.index_dir, exist_ok=True)
        self.index_path = os.path.join(_settings.index_dir, "veridoc.faiss")
        self.meta_path = os.path.join(_settings.index_dir, "veridoc_meta.json")
        self._index = None
        self._meta: dict[str, dict] = {}
        self._next_id = 0
        self._load()

    def _load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self._index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r") as f:
                payload = json.load(f)
                self._meta = payload.get("meta", {})
                self._next_id = payload.get("next_id", 0)
        else:
            base = faiss.IndexFlatIP(EMBEDDING_DIM)
            self._index = faiss.IndexIDMap2(base)
            self._meta = {}
            self._next_id = 0

    def _persist(self):
        faiss.write_index(self._index, self.index_path)
        with open(self.meta_path, "w") as f:
            json.dump({"meta": self._meta, "next_id": self._next_id}, f)

    def add(self, vectors: np.ndarray, chunk_ids: list[str], document_ids: list[str], labels: list[str]) -> list[int]:
        with _lock:
            ids = np.arange(self._next_id, self._next_id + len(chunk_ids)).astype("int64")
            self._index.add_with_ids(vectors, ids)
            for i, cid, did, label in zip(ids.tolist(), chunk_ids, document_ids, labels):
                self._meta[str(i)] = {"chunk_id": cid, "document_id": did, "source_label": label}
            self._next_id += len(chunk_ids)
            self._persist()
            return ids.tolist()

    def remove_by_document(self, document_id: str):
        with _lock:
            ids_to_remove = [int(k) for k, v in self._meta.items() if v["document_id"] == document_id]
            if ids_to_remove:
                self._index.remove_ids(np.array(ids_to_remove, dtype="int64"))
                for k in list(map(str, ids_to_remove)):
                    self._meta.pop(k, None)
                self._persist()

    def search(self, query_vector: np.ndarray, top_k: int = 5, document_ids: list[str] | None = None):
        with _lock:
            if self._index.ntotal == 0:
                return []
            fetch_k = min(max(top_k * 6, top_k), self._index.ntotal)
            scores, ids = self._index.search(query_vector.reshape(1, -1), fetch_k)
            results = []
            for score, idx in zip(scores[0], ids[0]):
                if idx == -1:
                    continue
                meta = self._meta.get(str(idx))
                if not meta:
                    continue
                if document_ids and meta["document_id"] not in document_ids:
                    continue
                results.append({"score": float(score), **meta})
                if len(results) >= top_k:
                    break
            return results


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
