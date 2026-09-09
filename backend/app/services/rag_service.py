"""Real retrieval-augmented generation: embed the question, search FAISS,
build a grounded context from only verified content, and require the model
to answer strictly from that context. Never sends the raw question straight
to the LLM without retrieval."""
import json
import logging
import re

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.models.document import Chunk, Document
from app.services.embedding_service import embed_query, embed_texts
from app.services.llm.factory import get_llm_provider
from app.services.vector_store import get_vector_store

logger = logging.getLogger("veridoc.rag")

CHUNK_SIZE_CHARS = 800
CHUNK_OVERLAP = 120
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s")

SYSTEM_PROMPT = """TASK: RAG_ANSWER
You answer the user's QUESTION using ONLY the passages in CONTEXT, which were
retrieved from a verified uploaded document. Never use outside knowledge and
never invent a fact, number, or citation that isn't supported by CONTEXT.

Write "answer" as a natural-language explanation that directly answers the
question, in your own words, synthesized from whatever CONTEXT passages are
relevant - as if explaining it to someone who hasn't read the document.
- Do NOT answer with just a heading, title, keyword, or isolated phrase (e.g.
  answering "Broadcast Routing" to "What is broadcast routing?" is wrong even
  if that phrase is the most relevant snippet) - explain the concept/fact
  using the surrounding supporting content instead.
- Do NOT paste raw fragments from CONTEXT together, and do NOT stitch together
  half-sentences from different passages. Write complete sentences of your
  own that convey the same information - the output must read as one
  coherent explanation, not a collage of quoted pieces.
- If more than one CONTEXT passage is relevant (e.g. the question asks about
  a trend across several data points, or several aspects of one topic),
  combine the *information* from all of them into one coherent answer -
  never their literal wording end-to-end.
- Match the answer's shape to the question: a definition/explanation for
  "what is X", a reason for "why is X needed", steps for "how does X work",
  a short bullet list for "advantages of X", a structured comparison for
  "compare X and Y".
- Be concise but complete: 2-4 sentences for a simple conceptual question,
  more only if the question genuinely needs it. No unnecessary padding.
- If CONTEXT does not contain enough information to answer, set "found" to
  false and "answer" to null - do not guess or partially answer.
- "confidence" (0.0-1.0) must reflect how directly and fully CONTEXT supports
  the answer you gave (1.0 = explicitly and fully supported, lower if you had
  to infer or if support is partial) - do not default to a fixed number.

Respond ONLY with JSON: {"answer": "string or null", "confidence": 0.0-1.0, "found": true|false}"""


class RagAnswer(BaseModel):
    answer: str | None = None
    confidence: float = 0.0
    found: bool = False


def chunk_text(text: str, size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Splits into ~`size`-char pieces, but snaps each cut to a sentence
    boundary (falling back to a word boundary) within the back half of the
    window, instead of slicing at a raw character offset. Naive char-offset
    slicing was producing chunks that started/ended mid-word or mid-sentence
    (e.g. "...to all" / "As networks grow..."), which then showed up as
    garbled evidence and, when an LLM or the offline demo mode tried to use
    that evidence, as disjointed, fragment-like answers."""
    text = text.strip()
    n = len(text)
    if n <= size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < n:
        end = min(start + size, n)
        if end < n:
            window_start = start + max(size // 2, 1)
            boundaries = [m.end() for m in _SENTENCE_BOUNDARY.finditer(text, window_start, end)]
            if boundaries:
                end = boundaries[-1]
            else:
                last_space = text.rfind(" ", window_start, end)
                if last_space != -1:
                    end = last_space
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(end - overlap, start + 1)  # always make forward progress
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
            "answer": "Not found in the uploaded document.",
            "sources": [],
            "confidence": 0.0,
            "grounded": False,
            "provider": get_llm_provider().name,
        }

    # Use everything retrieval judged relevant (bounded by the caller's top_k,
    # same as before - not blindly widened) as context, so multi-part
    # questions (e.g. "how did revenue change over three years") have enough
    # passages to synthesize an answer from. Previously this was hard-capped
    # to 3 regardless of top_k, which could starve exactly this kind of
    # question of the passages it needed.
    top_results = sorted(results, key=lambda r: r["score"], reverse=True)

    context_lines = [f"[{i+1}] ({r['source_label']}) {_lookup_chunk_text(db, r['chunk_id'])}" for i, r in enumerate(top_results)]
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
            "answer": "Not found in the uploaded document.",
            "sources": [],  # nothing was actually used, so nothing is shown as "evidence"
            "confidence": 0.0,
            "grounded": False,
            "provider": provider.name,
        }

    # Don't blindly trust the LLM's self-reported "confidence" - ground it in
    # how strong the actual retrieval match was, so a model that claims high
    # confidence off a weak/marginal retrieval hit doesn't produce a
    # misleadingly high number in the UI. This averages the model's own
    # (context-support) confidence with the top chunk's retrieval similarity.
    top_score = max(0.0, min(1.0, top_results[0]["score"])) if top_results else 0.0
    grounded_confidence = round((parsed.confidence + top_score) / 2, 2)

    # Show the sources that genuinely back the answer as evidence - capped
    # so the UI isn't flooded with low-relevance citations, but wide enough
    # (up to 4) to cover answers synthesized from several passages.
    sources = [{
        "label": r["source_label"],
        "document_id": r["document_id"],
        "evidence": _lookup_chunk_text(db, r["chunk_id"])[:280],
        "score": round(r["score"], 3),
    } for r in top_results[:4]]

    return {
        "answer": parsed.answer,
        "sources": sources,
        "confidence": grounded_confidence,
        "grounded": True,
        # Not used by the existing UI, but makes it possible to see in the
        # browser network tab / API response, unambiguously, whether an
        # answer actually came from OpenAI or from the offline mock provider -
        # this exact confusion has been the recurring root cause here.
        "provider": provider.name,
    }


def _lookup_chunk_text(db: Session, chunk_id: str) -> str:
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    return chunk.text if chunk else ""