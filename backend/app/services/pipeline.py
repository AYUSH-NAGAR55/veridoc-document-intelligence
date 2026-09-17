"""Orchestrates the full VeriDoc pipeline for a single document:

uploaded -> understanding -> extracting -> validating -> verifying -> indexing -> ready

Runs as a FastAPI background task so the upload endpoint returns immediately
and the UI can poll /documents/{id} for status.
"""
import logging

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.document import Document, ContentUnit, ProcessingStatus
from app.models.extraction import Extraction, ValidationResult, VerifiedValue
from app.models.review import ReviewItem
from app.services import extraction_service, validation_service, rag_service, summary_service, pii_service
from app.services.audit_service import log as audit_log
from app.services.confidence_service import needs_review
from app.services.duplicate_service import find_duplicate, hash_file
from app.services.processors.factory import get_processor

logger = logging.getLogger("veridoc.pipeline")


def _set_status(db: Session, document: Document, status: ProcessingStatus, message: str | None = None):
    document.status = status
    document.status_message = message
    db.commit()


def run_pipeline(document_id: str, owner_id: str):
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return

        try:
            _process_understanding(db, document, owner_id)
            _process_extraction_and_validation(db, document)
            _process_verification(db, document)
            _process_indexing(db, document)
            _set_status(db, document, ProcessingStatus.READY, "Document is ready.")
        except Exception as e:
            logger.exception("Pipeline failed for document %s", document_id)
            _set_status(db, document, ProcessingStatus.FAILED, f"Processing failed: {e}")
    finally:
        db.close()


def _process_understanding(db: Session, document: Document, owner_id: str):
    _set_status(db, document, ProcessingStatus.UNDERSTANDING, "Reading document content...")
    processor = get_processor(document.file_type)
    result = processor.process(document.stored_path)

    for idx, unit in enumerate(result.content_units):
        db.add(ContentUnit(
            document_id=document.id,
            content_type=unit.content_type,
            text=unit.text,
            table_data=unit.table_data,
            location=unit.location,
            unit_metadata=unit.metadata,
            order_index=idx,
        ))
    document.used_ocr = 1 if result.used_ocr else 0
    document.content_type = result.document_content_type
    db.commit()
    db.refresh(document)

    # Duplicate detection, now that we have text to compare
    full_text = _full_text(document)
    file_bytes = open(document.stored_path, "rb").read()
    dup_doc, score = find_duplicate(db, hash_file(file_bytes), full_text, owner_id)
    document.file_hash = hash_file(file_bytes)
    if dup_doc:
        document.duplicate_of = dup_doc.id
        document.duplicate_score = score
    db.commit()

    # PII scan (informational, non-blocking)
    findings = pii_service.detect_pii(full_text)
    document.pii_findings = findings[:100]
    db.commit()


def _process_extraction_and_validation(db: Session, document: Document):
    _set_status(db, document, ProcessingStatus.EXTRACTING, "Extracting structured information...")
    full_text = _full_text(document)
    tables_summary = _tables_summary(document)

    output = extraction_service.extract_fields(full_text, tables_summary)
    document.document_kind = output.document_kind
    db.commit()

    extraction_rows: list[Extraction] = []
    for field in output.fields:
        extraction = Extraction(
            document_id=document.id,
            field_name=field.field_name,
            field_value=field.field_value,
            value_type=field.value_type,
            confidence=field.confidence,
            source_location=field.source_location,
            evidence_text=field.evidence_text,
        )
        db.add(extraction)
        extraction_rows.append(extraction)
        audit_log(db, document.id, action="extracted", field_name=field.field_name,
                   after_value=field.field_value, actor="system")
    db.commit()
    for e in extraction_rows:
        db.refresh(e)

    _set_status(db, document, ProcessingStatus.VALIDATING, "Validating extracted values...")
    field_dicts = [{
        "field_name": e.field_name, "field_value": e.field_value,
        "value_type": e.value_type, "confidence": e.confidence,
    } for e in extraction_rows]

    outcomes = validation_service.run_validations(field_dicts)
    for outcome in outcomes:
        db.add(ValidationResult(
            document_id=document.id, rule_name=outcome.rule_name,
            passed=outcome.passed, message=outcome.message, fields_involved=outcome.fields_involved,
        ))
    db.commit()

    failed_fields = {f for o in outcomes if o.passed == "fail" for f in o.fields_involved}
    validation_messages = {f: o.message for o in outcomes if o.passed in ("fail", "warning") for f in o.fields_involved}

    for extraction in extraction_rows:
        field_failed = extraction.field_name in failed_fields
        review_needed, reason = needs_review(extraction.confidence, field_failed)
        if review_needed:
            db.add(ReviewItem(
                document_id=document.id, extraction_id=extraction.id,
                field_name=extraction.field_name, ai_value=extraction.field_value,
                confidence=extraction.confidence, source_location=extraction.source_location,
                evidence_text=extraction.evidence_text, reason=reason,
                validation_message=validation_messages.get(extraction.field_name),
            ))
        else:
            db.add(VerifiedValue(
                document_id=document.id, extraction_id=extraction.id,
                field_name=extraction.field_name, original_ai_value=extraction.field_value,
                verified_value=extraction.field_value, was_corrected="no", verification_status="verified",
                source_location=extraction.source_location,
            ))
            audit_log(db, document.id, action="verified", field_name=extraction.field_name,
                       after_value=extraction.field_value, actor="system",
                       reason="Auto-verified: confidence and validation both passed.")
    db.commit()


def _process_verification(db: Session, document: Document):
    _set_status(db, document, ProcessingStatus.VERIFYING, "Assembling verified knowledge...")
    extractions = document.extractions
    avg_conf = sum(e.confidence for e in extractions) / len(extractions) if extractions else 0.0
    validation_failed = any(v.passed == "fail" for v in document.validation_results)
    missing_expected = any(o.rule_name == "missing_field" for o in document.validation_results)

    full_text = _full_text(document)
    has_tables = any(u.content_type == "table" for u in document.content_units)

    score, checks = summary_service.compute_quality_score(
        has_text=bool(full_text.strip()), has_tables=has_tables, used_ocr=bool(document.used_ocr),
        validation_failed=validation_failed, avg_confidence=avg_conf, missing_expected=missing_expected,
    )
    document.quality_score = score
    document.quality_checks = checks
    document.summary = summary_service.generate_summary(full_text)
    document.suggested_questions = summary_service.generate_suggested_questions(
        [{"field_name": e.field_name, "field_value": e.field_value} for e in extractions]
    )
    db.commit()


def _process_indexing(db: Session, document: Document):
    _set_status(db, document, ProcessingStatus.INDEXING, "Building searchable knowledge index...")
    db.refresh(document)
    rag_service.index_document(db, document)


def _full_text(document: Document) -> str:
    return "\n".join(u.text for u in document.content_units if u.text)


def _tables_summary(document: Document) -> str:
    lines = []
    for u in document.content_units:
        if u.content_type == "table" and u.table_data:
            headers = u.table_data.get("headers", [])
            lines.append(" | ".join(headers))
            for row in u.table_data.get("rows", [])[:20]:
                lines.append(" | ".join(str(c) for c in row))
    return "\n".join(lines)
