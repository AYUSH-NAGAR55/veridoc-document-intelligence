"""Human review queue: Accept, Reject, Correct -- each action is written
to an immutable ReviewAudit row before the field itself is updated, so
the full history survives even after a field is corrected again later.
"""
import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("", response_model=list[schemas.FieldOut])
def get_review_queue(db: Session = Depends(get_db)):
    return (
        db.query(models.ExtractedField)
        .filter(models.ExtractedField.status == "pending")
        .order_by(models.ExtractedField.confidence.asc())
        .all()
    )


@router.post("/{field_id}/accept", response_model=schemas.FieldOut)
def accept_field(field_id: str, db: Session = Depends(get_db)):
    field = _get_field_or_404(db, field_id)
    db.add(models.ReviewAudit(
        field_id=field.id, action="accept",
        previous_value=field.field_value, new_value=field.field_value,
    ))
    field.status = "accepted"
    field.is_verified = True
    field.confidence = max(field.confidence, 0.95)
    field.corrected_at = datetime.datetime.utcnow()
    db.commit()
    _maybe_mark_document_ready(db, field.document_id)
    return field


@router.post("/{field_id}/reject", response_model=schemas.FieldOut)
def reject_field(field_id: str, payload: schemas.RejectFieldIn | None = None, db: Session = Depends(get_db)):
    field = _get_field_or_404(db, field_id)
    db.add(models.ReviewAudit(
        field_id=field.id, action="reject",
        previous_value=field.field_value, new_value=None,
        reviewer_note=(payload.reason if payload else None),
    ))
    field.status = "rejected"
    field.is_verified = False
    field.corrected_at = datetime.datetime.utcnow()
    db.commit()
    _maybe_mark_document_ready(db, field.document_id)
    return field


@router.post("/{field_id}/correct", response_model=schemas.FieldOut)
def correct_field(field_id: str, payload: schemas.CorrectFieldIn, db: Session = Depends(get_db)):
    field = _get_field_or_404(db, field_id)
    db.add(models.ReviewAudit(
        field_id=field.id, action="correct",
        previous_value=field.field_value, new_value=payload.corrected_value,
    ))
    # original_ai_value is set once at creation and never touched again --
    # this is what makes the AI-value-vs-verified-value distinction durable.
    field.field_value = payload.corrected_value
    field.status = "corrected"
    field.is_verified = True
    field.confidence = 0.99
    field.corrected_at = datetime.datetime.utcnow()
    db.commit()
    _maybe_mark_document_ready(db, field.document_id)
    return field


def _get_field_or_404(db: Session, field_id: str) -> models.ExtractedField:
    field = db.query(models.ExtractedField).get(field_id)
    if not field:
        raise HTTPException(404, "Field not found.")
    return field


def _maybe_mark_document_ready(db: Session, document_id: str):
    remaining = (
        db.query(models.ExtractedField)
        .filter(models.ExtractedField.document_id == document_id, models.ExtractedField.status == "pending")
        .count()
    )
    if remaining == 0:
        doc = db.query(models.Document).get(document_id)
        if doc and doc.status == models.DocStatus.needs_review:
            doc.status = models.DocStatus.ready
            db.commit()
