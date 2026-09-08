import hashlib
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models.document import Document

SIMILARITY_THRESHOLD = 0.90


def hash_file(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def find_duplicate(db: Session, file_hash: str, extracted_text: str, owner_id: str) -> tuple[Document | None, float]:
    exact = db.query(Document).filter(Document.file_hash == file_hash, Document.owner_id == owner_id).first()
    if exact:
        return exact, 1.0

    if not extracted_text.strip():
        return None, 0.0

    candidates = db.query(Document).filter(Document.status != "failed", Document.owner_id == owner_id).limit(50).all()
    best_doc, best_score = None, 0.0
    sample = extracted_text[:3000]
    for doc in candidates:
        doc_text = " ".join((u.text or "") for u in doc.content_units)[:3000]
        if not doc_text:
            continue
        score = SequenceMatcher(None, sample, doc_text).ratio()
        if score > best_score:
            best_score, best_doc = score, doc

    if best_score >= SIMILARITY_THRESHOLD:
        return best_doc, best_score
    return None, best_score
