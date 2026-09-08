from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.schemas import CompareRequest
from app.services.comparison_service import compare_documents

router = APIRouter(tags=["compare"])


@router.post("/documents/compare")
def compare(payload: CompareRequest, db: Session = Depends(get_db)):
    doc_a = db.query(Document).filter(Document.id == payload.document_id_a).first()
    doc_b = db.query(Document).filter(Document.id == payload.document_id_b).first()
    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents were not found.")
    return compare_documents(doc_a, doc_b)
