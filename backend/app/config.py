"""Central configuration, all overridable via environment variables.

Nothing in this file should be hard-coded elsewhere in the app — if a
component needs a model name, URL, or path, it should import from here.
"""
import os

# --- LLM (Ollama) ---
# Ollama is a local server you run yourself: https://ollama.com
# After installing it, pull a model once with e.g. `ollama pull llama3`.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT_SECONDS = float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "60"))

# --- Embeddings ---
# Any Sentence-Transformers model name works here. Downloaded once from
# Hugging Face on first use and cached locally afterwards.
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Storage ---
STORAGE_DIR = os.environ.get("VERIDOC_STORAGE_DIR", os.path.join(os.path.dirname(__file__), "storage"))
FAISS_INDEX_DIR = os.environ.get("VERIDOC_FAISS_DIR", os.path.join(os.path.dirname(__file__), "faiss_index"))

# --- Upload limits ---
MAX_UPLOAD_MB = float(os.environ.get("VERIDOC_MAX_UPLOAD_MB", "25"))
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".csv", ".xlsx", ".xls", ".json",
    ".png", ".jpg", ".jpeg",
}

# --- Validation / review ---
REVIEW_THRESHOLD = float(os.environ.get("VERIDOC_REVIEW_THRESHOLD", "0.70"))

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
