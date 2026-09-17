from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..pipeline import qa

router = APIRouter(prefix="/api/documents", tags=["chat"])

_PROCESSING = {
    models.DocStatus.uploaded, models.DocStatus.understanding, models.DocStatus.extracting,
    models.DocStatus.validating, models.DocStatus.verifying, models.DocStatus.indexing,
}


@router.post("/{document_id}/ask", response_model=schemas.AskOut)
def ask_question(document_id: str, payload: schemas.AskIn, db: Session = Depends(get_db)):
    doc = db.query(models.Document).get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    if doc.status in _PROCESSING:
        raise HTTPException(409, "Document is still processing -- try again shortly.")

    answer = qa.answer_question(document_id, payload.question)
    return schemas.AskOut(
        answer=answer.text,
        found=answer.found,
        confidence=answer.confidence,
        sources=[
            schemas.SourceOut(location=schemas.LocationOut(**s["location"]), text=s["text"], score=s["score"])
            for s in answer.sources
        ],
    )
