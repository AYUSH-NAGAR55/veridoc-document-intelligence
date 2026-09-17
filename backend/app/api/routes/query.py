from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.query import QueryLog
from app.schemas.schemas import QueryRequest
from app.services.rag_service import answer_question

router = APIRouter(tags=["query"])


@router.post("/query")
def query(payload: QueryRequest, db: Session = Depends(get_db)):
    result = answer_question(db, payload.question, payload.document_ids, payload.top_k)
    db.add(QueryLog(
        question=payload.question, answer=result["answer"], document_ids=payload.document_ids,
        sources=result["sources"], confidence=result["confidence"], grounded="yes" if result["grounded"] else "no",
    ))
    db.commit()
    return result


@router.post("/documents/{document_id}/query")
def query_single_document(document_id: str, payload: QueryRequest, db: Session = Depends(get_db)):
    result = answer_question(db, payload.question, [document_id], payload.top_k)
    db.add(QueryLog(
        question=payload.question, answer=result["answer"], document_ids=[document_id],
        sources=result["sources"], confidence=result["confidence"], grounded="yes" if result["grounded"] else "no",
    ))
    db.commit()
    return result
