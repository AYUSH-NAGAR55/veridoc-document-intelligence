from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_owner_id
from app.database import get_db
from app.models.document import Document
from app.models.query import QueryLog
from app.schemas.schemas import QueryRequest
from app.services.rag_service import answer_question

router = APIRouter(tags=["query"])


def _resolve_owned_document_ids(db: Session, owner_id: str, requested_ids: list[str] | None) -> list[str]:
    """Turns whatever the client asked for into a document_id list that is
    GUARANTEED to only contain documents owned by this owner_id.

    - No IDs requested -> scope to every document this owner has (never "all
      documents globally", which was the actual data leak).
    - Specific IDs requested -> intersect with owned IDs, so passing someone
      else's document ID (guessed, enumerated, or otherwise) silently yields
      nothing for that ID rather than leaking their content.
    """
    owned_ids = {d.id for d in db.query(Document.id).filter(Document.owner_id == owner_id).all()}
    if requested_ids:
        return [doc_id for doc_id in requested_ids if doc_id in owned_ids]
    return list(owned_ids)


@router.post("/query")
def query(payload: QueryRequest, db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)):
    scoped_ids = _resolve_owned_document_ids(db, owner_id, payload.document_ids)
    if not scoped_ids:
        result = {
            "answer": "Not found in the uploaded document.",
            "sources": [], "confidence": 0.0, "grounded": False,
        }
    else:
        result = answer_question(db, payload.question, scoped_ids, payload.top_k)

    db.add(QueryLog(
        owner_id=owner_id, question=payload.question, answer=result["answer"], document_ids=scoped_ids,
        sources=result["sources"], confidence=result["confidence"], grounded="yes" if result["grounded"] else "no",
    ))
    db.commit()
    return result


@router.post("/documents/{document_id}/query")
def query_single_document(document_id: str, payload: QueryRequest, db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)):
    document = db.query(Document).filter(Document.id == document_id, Document.owner_id == owner_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' was not found.")

    result = answer_question(db, payload.question, [document_id], payload.top_k)
    db.add(QueryLog(
        owner_id=owner_id, question=payload.question, answer=result["answer"], document_ids=[document_id],
        sources=result["sources"], confidence=result["confidence"], grounded="yes" if result["grounded"] else "no",
    ))
    db.commit()
    return result
