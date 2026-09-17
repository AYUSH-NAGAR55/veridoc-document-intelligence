"""Document upload, listing, detail, and deletion (single + bulk).

Deletion is the one place correctness really matters: a document's file
on disk, its DB rows (cascaded via SQLAlchemy relationships), and its
FAISS vectors all have to go together, or the RAG index ends up with
stale, orphaned entries pointing at a document that no longer exists.
"""
import os
import shutil
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from .. import models, schemas, config
from ..database import get_db
from ..pipeline import orchestrator
from ..embeddings import vector_index

router = APIRouter(prefix="/api/documents", tags=["documents"])

os.makedirs(config.STORAGE_DIR, exist_ok=True)


@router.post("", response_model=schemas.DocumentOut)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in config.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            400,
            f"'{ext or 'unknown'}' isn't a supported format. "
            f"Supported: {', '.join(sorted(config.SUPPORTED_EXTENSIONS))}",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > config.MAX_UPLOAD_MB:
        raise HTTPException(400, f"File is {size_mb:.1f}MB, which is over the {config.MAX_UPLOAD_MB}MB limit.")

    doc = models.Document(
        filename=file.filename, file_type=ext.lstrip("."), status=models.DocStatus.uploaded,
        size_bytes=len(contents),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Storage filename is UUID-based, never the user-supplied name, so an
    # uploaded filename can't be used for path traversal or to overwrite
    # another file on disk.
    safe_name = f"{doc.id}_{uuid.uuid4().hex[:6]}{ext}"
    dest_path = os.path.join(config.STORAGE_DIR, safe_name)
    with open(dest_path, "wb") as f:
        f.write(contents)

    background_tasks.add_task(_run_pipeline, doc.id, dest_path)
    return doc


def _run_pipeline(document_id: str, file_path: str):
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        orchestrator.process_document(db, document_id, file_path)
    finally:
        db.close()


@router.get("", response_model=list[schemas.DocumentOut])
def list_documents(search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Document)
    if search:
        query = query.filter(models.Document.filename.ilike(f"%{search}%"))
    return query.order_by(models.Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=schemas.DocumentDetailOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    out = schemas.DocumentDetailOut.model_validate(doc)
    units_by_index = {u.unit_index: u for u in doc.content_units}
    for cu in out.content_units:
        source = units_by_index.get(cu.unit_index)
        if source:
            cu.preview = (source.raw_text or "")[:220]
    return out


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    _delete_document_fully(db, doc)
    return {"ok": True}


@router.post("/bulk-delete")
def bulk_delete(payload: schemas.BulkDeleteIn, db: Session = Depends(get_db)):
    deleted = []
    for document_id in payload.document_ids:
        doc = db.query(models.Document).get(document_id)
        if doc:
            _delete_document_fully(db, doc)
            deleted.append(document_id)
    return {"deleted": deleted}


def _delete_document_fully(db: Session, doc: models.Document):
    """Removes the uploaded file, every DB row (via cascade), and every
    FAISS vector for this document -- nothing left orphaned.
    """
    for f in os.listdir(config.STORAGE_DIR):
        if f.startswith(doc.id + "_"):
            try:
                os.remove(os.path.join(config.STORAGE_DIR, f))
            except OSError:
                pass
    vector_index.remove_document(doc.id)
    db.delete(doc)   # cascades to content_units, fields (+ their audit rows), chunks
    db.commit()
