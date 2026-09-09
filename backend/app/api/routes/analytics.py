from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_owner_id
from app.database import get_db
from app.models.document import Document
from app.models.review import ReviewItem
from app.models.query import QueryLog

router = APIRouter(tags=["analytics"])


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)):
    documents = db.query(Document).filter(Document.owner_id == owner_id).all()
    document_ids = {d.id for d in documents}

    review_items = [i for d in documents for i in d.review_items] if documents else []
    recent_queries = (
        db.query(QueryLog)
        .filter(QueryLog.owner_id == owner_id)
        .order_by(QueryLog.created_at.desc())
        .limit(10)
        .all()
    )

    total = len(documents)
    verified = len([d for d in documents if d.status.value == "ready"])
    pending_review = len([i for i in review_items if i.status == "pending"])
    rejected = len([i for i in review_items if i.status == "rejected"])

    all_confidences = [e.confidence for d in documents for e in d.extractions]
    avg_confidence = round(sum(all_confidences) / len(all_confidences), 2) if all_confidences else 0.0

    validation_issues = sum(1 for d in documents for v in d.validation_results if v.passed == "fail")

    by_type = Counter(d.file_type.value for d in documents)

    recent_documents = sorted(documents, key=lambda d: d.created_at, reverse=True)[:8]

    return {
        "documents_processed": total,
        "verified_documents": verified,
        "pending_reviews": pending_review,
        "rejected_items": rejected,
        "average_confidence": avg_confidence,
        "validation_issues": validation_issues,
        "documents_by_type": dict(by_type),
        "recent_documents": [d.to_dict() for d in recent_documents],
        "recent_queries": [q.to_dict() for q in recent_queries],
    }
