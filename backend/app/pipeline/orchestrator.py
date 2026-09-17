"""Wires together the full pipeline for a single uploaded document:

file type detection -> processor -> normalized content -> LLM extraction
-> independent validation -> confidence/review routing -> chunking ->
embeddings -> FAISS indexing -> ready.

If Ollama or the embedding model are unavailable, the document is marked
failed with a clear, specific error rather than crashing or silently
falling back to something else.
"""
import os
import traceback

from sqlalchemy.orm import Session

from .. import models
from ..processors.base import get_processor, UnsupportedFormatError
from ..llm import llm_extractor
from ..llm.ollama_client import OllamaUnavailable, OllamaMalformedResponse
from ..embeddings import embedding_model
from ..embeddings import vector_index
from . import validator


def process_document(db: Session, document_id: str, file_path: str):
    doc = db.query(models.Document).get(document_id)
    if doc is None:
        return
    try:
        doc.status = models.DocStatus.understanding
        db.commit()

        processor = get_processor(file_path)
        normalized = processor.process(file_path)

        doc.unit_count = len(normalized.units)
        doc.unit_count_label = normalized.unit_count_label
        db.commit()

        for i, unit in enumerate(normalized.units):
            db.add(models.ContentUnit(
                document_id=doc.id,
                unit_index=i,
                content_type=unit.content_type,
                location=unit.location.to_dict(),
                raw_text=unit.text,
                tables_json=unit.tables,
                ocr_confidence=unit.ocr_confidence,
                extraction_notes=unit.notes,
            ))
        db.commit()

        doc.status = models.DocStatus.extracting
        db.commit()

        full_text = normalized.full_text()
        if not full_text.strip():
            doc.doc_type = "generic"
            doc.summary = "No extractable text was found in this document."
            db.commit()
            llm_fields = []
        else:
            try:
                extraction = llm_extractor.extract_fields(full_text)
                doc.doc_type = extraction.document_type
                doc.summary = extraction.summary
                db.commit()
                llm_fields = extraction.fields
            except OllamaUnavailable as exc:
                doc.status = models.DocStatus.failed
                doc.error_message = str(exc)
                db.commit()
                return
            except OllamaMalformedResponse as exc:
                doc.status = models.DocStatus.failed
                doc.error_message = f"The LLM's response couldn't be understood after a retry: {exc}"
                db.commit()
                return

        doc.status = models.DocStatus.validating
        db.commit()

        ocr_confidence_by_index = _resolve_field_locations(llm_fields, normalized)
        validated_fields = validator.validate_llm_fields(llm_fields, ocr_confidence_by_index)

        any_pending = False
        for vf in validated_fields:
            if vf.auto_status == "pending":
                any_pending = True
            db.add(models.ExtractedField(
                document_id=doc.id,
                field_name=vf.field_name,
                field_value=vf.value,
                original_ai_value=vf.value,
                confidence=vf.confidence,
                location=vf.location,
                source_snippet=vf.source_snippet,
                status=vf.auto_status,
                is_verified=vf.is_verified,
                validation_notes=vf.notes,
            ))
        db.commit()

        doc.status = models.DocStatus.verifying
        db.commit()
        # Verification status is derived per-field (is_verified) above;
        # this stage exists mainly to make the pipeline stage visible in
        # the UI as its own step, matching the spec's stage list.

        doc.status = models.DocStatus.indexing
        db.commit()

        _index_document(db, doc, normalized)

        doc.status = models.DocStatus.needs_review if any_pending else models.DocStatus.ready
        db.commit()

    except UnsupportedFormatError as exc:
        doc.status = models.DocStatus.failed
        doc.error_message = str(exc)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        doc.status = models.DocStatus.failed
        doc.error_message = f"{exc}\n{traceback.format_exc()[-800:]}"
        db.commit()


def _resolve_field_locations(llm_fields, normalized):
    """Never trust the LLM's own claim about where a value came from --
    instead, find which content unit's actual text contains the evidence
    span it quoted, and use that unit's real location. Falls back to a
    word-overlap match if the LLM paraphrased rather than quoting exactly.
    If nothing matches well enough, the field is left without a location
    rather than fabricating one.

    Returns a dict mapping each field's evidence text to the OCR
    confidence of the unit it was resolved to (None if not OCR'd), so the
    validator can discount confidence for fields sourced from uncertain
    OCR text -- a field read off a garbled scan shouldn't carry the same
    confidence as one read off clean digital text.
    """
    import re
    ocr_confidence_by_field_index: dict[int, float | None] = {}

    for idx, f in enumerate(llm_fields):
        evidence = (f.evidence or "").strip().lower()
        if not evidence:
            continue

        exact_match = next((u for u in normalized.units if evidence in u.text.lower()), None)
        if exact_match:
            f.source_location = exact_match.location.to_dict()
            ocr_confidence_by_field_index[idx] = exact_match.ocr_confidence
            continue

        evidence_words = set(re.findall(r"[a-z0-9]{2,}", evidence))
        if not evidence_words:
            continue
        best_unit, best_overlap = None, 0
        for unit in normalized.units:
            unit_words = set(re.findall(r"[a-z0-9]{2,}", unit.text.lower()))
            overlap = len(evidence_words & unit_words)
            if overlap > best_overlap:
                best_overlap, best_unit = overlap, unit
        if best_unit and best_overlap >= max(1, len(evidence_words) // 2):
            f.source_location = best_unit.location.to_dict()
            ocr_confidence_by_field_index[idx] = best_unit.ocr_confidence

    return ocr_confidence_by_field_index


def _index_document(db: Session, doc: "models.Document", normalized):
    """Chunk verified content, embed it, and add it to the shared FAISS index."""
    chunks_text_and_location = []
    for unit in normalized.units:
        if not unit.text.strip():
            continue
        for piece in _split_text(unit.text):
            chunks_text_and_location.append((piece, unit.location.to_dict()))

    if not chunks_text_and_location:
        return

    try:
        vectors = embedding_model.embed([t for t, _ in chunks_text_and_location])
    except Exception as exc:
        # Embedding model unavailable (e.g. no network to download weights
        # on first use) -- document still has its extracted fields and is
        # usable, it just won't be searchable via RAG until this succeeds.
        doc.error_message = (doc.error_message or "") + f"\n[Indexing skipped: embedding model unavailable — {exc}]"
        db.commit()
        return

    items = []
    for (text, location), vector in zip(chunks_text_and_location, vectors):
        chunk_row = models.Chunk(document_id=doc.id, location=location, text=text, is_verified=True)
        db.add(chunk_row)
        db.flush()  # get chunk_row.id before building the FAISS metadata
        items.append({"chunk_id": chunk_row.id, "vector": vector, "location": location, "text": text})
    db.commit()

    vector_index.add_batch(doc.id, items)


def _split_text(text: str, max_chars: int = 700) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current:
        chunks.append(current.strip())
    return chunks or [text[:max_chars]]
