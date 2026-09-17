import os
import re
import uuid

ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".csv": "csv",
    ".json": "json",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class UnsupportedFileType(Exception):
    pass


class FileTooLarge(Exception):
    pass


def sanitize_filename(filename: str) -> str:
    """Strip any path components and unsafe characters to prevent path traversal."""
    base = os.path.basename(filename or "file")
    base = _SAFE_NAME_RE.sub("_", base)
    return base[:200] or "file"


def validate_extension(filename: str) -> str:
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileType(f"'{ext}' is not a supported file type.")
    return ALLOWED_EXTENSIONS[ext]


def build_storage_path(upload_dir: str, original_filename: str) -> tuple[str, str]:
    """Returns (safe_stored_path, safe_display_filename). The stored filename is
    randomized so two uploads can never collide or overwrite each other."""
    safe_name = sanitize_filename(original_filename)
    ext = os.path.splitext(safe_name)[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(upload_dir, stored_name)
    # Defense in depth: ensure resolved path stays inside upload_dir
    resolved_dir = os.path.realpath(upload_dir)
    resolved_path = os.path.realpath(stored_path)
    if not resolved_path.startswith(resolved_dir):
        raise ValueError("Invalid storage path")
    return stored_path, safe_name
