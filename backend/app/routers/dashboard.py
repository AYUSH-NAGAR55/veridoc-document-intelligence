from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..embeddings import vector_index

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    total = db.query(models.Document).count()
    processing_statuses = [
        models.DocStatus.uploaded, models.DocStatus.understanding, models.DocStatus.extracting,
        models.DocStatus.validating, models.DocStatus.verifying, models.DocStatus.indexing,
    ]
    processing = db.query(models.Document).filter(models.Document.status.in_(processing_statuses)).count()
    ready = db.query(models.Document).filter(models.Document.status == models.DocStatus.ready).count()
    needs_review = db.query(models.Document).filter(models.Document.status == models.DocStatus.needs_review).count()
    failed = db.query(models.Document).filter(models.Document.status == models.DocStatus.failed).count()

    total_fields = db.query(models.ExtractedField).count()
    verified_fields = db.query(models.ExtractedField).filter(models.ExtractedField.is_verified == True).count()  # noqa: E712
    pending_fields = db.query(models.ExtractedField).filter(models.ExtractedField.status == "pending").count()

    recent_documents = (
        db.query(models.Document).order_by(models.Document.created_at.desc()).limit(6).all()
    )
    recent_reviews = (
        db.query(models.ReviewAudit).order_by(models.ReviewAudit.created_at.desc()).limit(6).all()
    )

    return schemas.DashboardOut(
        total_documents=total,
        processing_documents=processing,
        ready_documents=ready,
        needs_review_documents=needs_review,
        failed_documents=failed,
        total_fields=total_fields,
        verified_fields=verified_fields,
        pending_review_fields=pending_fields,
        indexed_vectors=vector_index.total_vectors(),
        recent_documents=recent_documents,
        recent_reviews=recent_reviews,
    )
