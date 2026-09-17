"""Local filesystem storage. Kept behind this tiny interface so swapping in
S3/GCS later only requires a new implementation of the same three methods."""
import os

from app.config import get_settings

_settings = get_settings()


class LocalStorage:
    def save(self, path: str, content: bytes) -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def delete(self, path: str) -> None:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def read(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()


def get_storage() -> LocalStorage:
    return LocalStorage()
