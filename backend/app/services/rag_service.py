"""Real retrieval-augmented generation: embed the question, search FAISS,
build a grounded context from only verified content, and require the model
to answer strictly from that context. Never sends the raw question straight
to the LLM without retrieval."""
import json
import logging

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.models.document import Chunk, Document
from app.services.embedding_service import embed_query, embed_texts
from app.services.llm.factory import get_llm_provider
from app.services.vector_store import get_vector_store

logger = logging.getLogger("veridoc.rag")

CHUNK_SIZE_CHARS = 800
CHUNK_OVERLAP = 120

SYSTEM_PROMPT = """TASK: RAG_ANSWER
You answer questions using ONLY the provided CONTEXT, which was retrieved from
verified documents. Never use outside knowledge. Never invent a citation.

If the context does not contain the answer, respond with found=false.

Respond ONLY with JSON: {"answer": "string or null", "confidence": 0.0-1.0, "found": true|false}"""


class RagAnswer(BaseModel):
    answer: str | None = None
    confidence: float = 0.0
    found: bool = False


def chunk_text(text: str, size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else end
    return chunks


def index_document(db: Session, document: Document):
    """Chunk verified content and push embeddings into the vector store."""
    from app.models.extraction import VerifiedValue

    store = get_vector_store()
    store.remove_by_document(document.id)  # avoid duplicate indexing on re-index

    texts, locations, labels = [], [], []

    for unit in document.content_units:
        if unit.content_type == "table" and unit.table_data:
            table_text = _table_to_text(unit.table_data)
            for piece in chunk_text(table_text):
                texts.append(piece)
                locations.append(unit.location)
                labels.append(_label_for(document, unit.location))
        elif unit.text:
            for piece in chunk_text(unit.text):
                texts.append(piece)
                locations.append(unit.location)
                labels.append(_label_for(document, unit.location))

    verified: list[VerifiedValue] = db.query(VerifiedValue).filter(
        VerifiedValue.document_id == document.id,
        VerifiedValue.verification_status == "verified",
    ).all()
    for v in verified:
        texts.append(f"{v.field_name}: {v.verified_value}")
        locations.append(v.source_location or {})
        labels.append(_label_for(document, v.source_location or {}, prefix="Verified"))

    if not texts:
        return 0

    vectors = embed_texts(texts)
    chunk_ids, document_ids = [], []
    for text, location, label in zip(texts, locations, labels):
        chunk = Chunk(document_id=document.id, text=text, location=location, source_label=label)
        db.add(chunk)
        db.flush()
        chunk_ids.append(chunk.id)
        document_ids.append(document.id)
    db.commit()

    store.add(vectors, chunk_ids, document_ids, labels)
    return len(texts)


def _table_to_text(table_data: dict) -> str:
    headers = table_data.get("headers", [])
    lines = [" | ".join(headers)]
    for row in table_data.get("rows", []):
        lines.append(" | ".join(str(c) for c in row))
    return "\n".join(lines)


def _label_for(document: Document, location: dict, prefix: str | None = None) -> str:
    parts = [prefix] if prefix else []
    parts.append(document.filename)
    if not location:
        return " - ".join(p for p in parts if p)
    if "page" in location:
        parts.append(f"Page {location['page']}")
    if "section" in location:
        parts.append(str(location["section"]))
    if "sheet" in location:
        loc = f"Sheet {location['sheet']}"
        if "row" in location:
            loc += f", Row {location['row']}"
        parts.append(loc)
    if "line" in location:
        parts.append(f"Line {location['line']}")
    if "json_path" in location:
        parts.append(str(location["json_path"]))
    return " - ".join(p for p in parts if p)


def answer_question(db: Session, question: str, document_ids: list[str] | None = None, top_k: int = 5) -> dict:
    store = get_vector_store()
    q_vector = embed_query(question)
    results = store.search(q_vector, top_k=top_k, document_ids=document_ids)

    if not results:
        return {
            "answer": "The requested information could not be found in the available documents.",
            "sources": [],
            "confidence": 0.0,
            "grounded": False,
        }

    context_lines = [f"[{i+1}] ({r['source_label']}) {_lookup_chunk_text(db, r['chunk_id'])}" for i, r in enumerate(results)]
    context = "\n".join(context_lines)

    provider = get_llm_provider()
    user_prompt = f"QUESTION\n{question}\n\nCONTEXT\n{context}"

    try:
        raw = provider.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
        parsed = RagAnswer.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError, Exception) as e:  # noqa: BLE001
        logger.warning("RAG answer parsing failed: %s", e)
        parsed = RagAnswer(found=False)

    if not parsed.found or not parsed.answer:
        return {
            "answer": "The requested information could not be found in the available documents.",
            "sources": [{"label": r["source_label"], "document_id": r["document_id"]} for r in results[:2]],
            "confidence": 0.0,
            "grounded": False,
        }

    sources = [{
        "label": r["source_label"],
        "document_id": r["document_id"],
        "evidence": _lookup_chunk_text(db, r["chunk_id"])[:280],
        "score": round(r["score"], 3),
    } for r in results]

    return {
        "answer": parsed.answer,
        "sources": sources,
        "confidence": round(parsed.confidence, 2),
        "grounded": True,
    }


def _lookup_chunk_text(db: Session, chunk_id: str) -> str:
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    return chunk.text if chunk else ""
