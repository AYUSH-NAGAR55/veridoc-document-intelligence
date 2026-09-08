from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owner_id
from app.database import get_db
from app.models.document import Document
from app.models.review import ReviewItem
from app.models.extraction import VerifiedValue
from app.schemas.schemas import ReviewActionRequest, ReviewCorrectionRequest
from app.services.audit_service import log as audit_log

router = APIRouter(prefix="/review-queue", tags=["review"])


@router.get("")
def list_review_queue(db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id), status: str = "pending"):
    query = db.query(ReviewItem).join(Document, ReviewItem.document_id == Document.id).filter(Document.owner_id == owner_id)
    if status != "all":
        query = query.filter(ReviewItem.status == status)
    items = query.order_by(ReviewItem.created_at.desc()).all()
    return [i.to_dict() for i in items]


def _get_item(db: Session, item_id: str, owner_id: str) -> ReviewItem:
    # Joins through Document so a review item can only ever be fetched/mutated
    # by the owner of the document it belongs to - closes the IDOR path where
    # someone could accept/correct/reject another user's pending item just by
    # guessing or enumerating item IDs.
    item = (
        db.query(ReviewItem)
        .join(Document, ReviewItem.document_id == Document.id)
        .filter(ReviewItem.id == item_id, Document.owner_id == owner_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found.")
    if item.status != "pending":
        raise HTTPException(status_code=400, detail="This review item has already been resolved.")
    return item


@router.post("/{item_id}/accept")
def accept_item(item_id: str, payload: ReviewActionRequest, db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)):
    item = _get_item(db, item_id, owner_id)
    item.status = "accepted"
    item.reviewer_note = payload.reviewer_note
    item.resolved_at = datetime.now(timezone.utc)

    db.add(VerifiedValue(
        document_id=item.document_id, extraction_id=item.extraction_id, field_name=item.field_name,
        original_ai_value=item.ai_value, verified_value=item.ai_value, was_corrected="no",
        verification_status="verified", source_location=item.source_location,
    ))
    audit_log(db, item.document_id, action="accepted", field_name=item.field_name,
              before_value=item.ai_value, after_value=item.ai_value, actor="reviewer", reason=payload.reviewer_note)
    db.commit()
    return item.to_dict()


@router.post("/{item_id}/correct")
def correct_item(item_id: str, payload: ReviewCorrectionRequest, db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)):
    item = _get_item(db, item_id, owner_id)
    item.status = "corrected"
    item.corrected_value = payload.corrected_value
    item.reviewer_note = payload.reviewer_note
    item.resolved_at = datetime.now(timezone.utc)

    db.add(VerifiedValue(
        document_id=item.document_id, extraction_id=item.extraction_id, field_name=item.field_name,
        original_ai_value=item.ai_value, verified_value=payload.corrected_value, was_corrected="yes",
        verification_status="verified", source_location=item.source_location,
    ))
    audit_log(db, item.document_id, action="corrected", field_name=item.field_name,
              before_value=item.ai_value, after_value=payload.corrected_value, actor="reviewer",
              reason=payload.reviewer_note)
    db.commit()
    return item.to_dict()


@router.post("/{item_id}/reject")
def reject_item(item_id: str, payload: ReviewActionRequest, db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)):
    item = _get_item(db, item_id, owner_id)
    item.status = "rejected"
    item.reviewer_note = payload.reviewer_note
    item.resolved_at = datetime.now(timezone.utc)

    db.add(VerifiedValue(
        document_id=item.document_id, extraction_id=item.extraction_id, field_name=item.field_name,
        original_ai_value=item.ai_value, verified_value=None, was_corrected="no",
        verification_status="rejected", source_location=item.source_location,
    ))
    audit_log(db, item.document_id, action="rejected", field_name=item.field_name,
              before_value=item.ai_value, after_value=None, actor="reviewer", reason=payload.reviewer_note)
    db.commit()
    return item.to_dict()
