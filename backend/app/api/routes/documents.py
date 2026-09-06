from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import DocumentNotFound
from app.core.security import UnsupportedFileType, build_storage_path, validate_extension
from app.database import get_db
from app.models.document import Document, ProcessingStatus, DocumentType
from app.services.audit_service import log as audit_log
from app.services.pipeline import run_pipeline
from app.services.storage import get_storage
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


@router.get("")
def list_documents(
    db: Session = Depends(get_db),
    search: str | None = None,
    file_type: str | None = None,
    status: str | None = None,
):
    query = db.query(Document)
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))
    if file_type:
        query = query.filter(Document.file_type == file_type)
    if status:
        query = query.filter(Document.status == status)
    documents = query.order_by(Document.created_at.desc()).all()
    return [d.to_dict() for d in documents]


@router.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        doc_type_value = validate_extension(file.filename)
    except UnsupportedFileType as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_size_mb}MB upload limit.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    stored_path, safe_name = build_storage_path(settings.upload_dir, file.filename)
    get_storage().save(stored_path, content)

    document = Document(
        filename=safe_name,
        stored_path=stored_path,
        file_type=DocumentType(doc_type_value),
        size_bytes=len(content),
        status=ProcessingStatus.UPLOADED,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    audit_log(db, document.id, action="extracted", reason="Document uploaded.", actor="system")

    background_tasks.add_task(run_pipeline, document.id)
    return {"id": document.id, "filename": document.filename, "status": document.status.value}


@router.get("/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)
    return document.to_dict()


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)

    get_vector_store().remove_by_document(document_id)
    get_storage().delete(document.stored_path)
    db.delete(document)  # cascades to content_units, extractions, review_items, chunks, verified_values, audit_logs
    db.commit()
    return {"deleted": True, "id": document_id}


@router.post("/delete-batch")
def delete_documents(ids: list[str], db: Session = Depends(get_db)):
    deleted = []
    for document_id in ids:
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            get_vector_store().remove_by_document(document_id)
            get_storage().delete(document.stored_path)
            db.delete(document)
            deleted.append(document_id)
    db.commit()
    return {"deleted": deleted}


@router.get("/{document_id}/content")
def get_document_content(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)
    return [u.to_dict() for u in sorted(document.content_units, key=lambda u: u.order_index)]


@router.get("/{document_id}/extractions")
def get_extractions(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)
    return {
        "extractions": [e.to_dict() for e in document.extractions],
        "verified_values": [v.to_dict() for v in document.verified_values],
    }


@router.get("/{document_id}/validation")
def get_validation(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)
    return [v.to_dict() for v in document.validation_results]


@router.get("/{document_id}/audit")
def get_audit(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)
    return [a.to_dict() for a in sorted(document.audit_logs, key=lambda a: a.created_at)]


@router.get("/{document_id}/anomalies")
def get_anomalies(document_id: str, db: Session = Depends(get_db)):
    from app.services.anomaly_service import detect_anomalies
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)
    return detect_anomalies(db, document)


@router.post("/{document_id}/index")
def reindex_document(document_id: str, db: Session = Depends(get_db)):
    from app.services.rag_service import index_document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)
    count = index_document(db, document)
    return {"chunks_indexed": count}


@router.get("/{document_id}/export")
def export_document(document_id: str, format: str = Query("json", pattern="^(json|csv)$"), db: Session = Depends(get_db)):
    import csv
    import io
    from fastapi.responses import JSONResponse, StreamingResponse

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFound(document_id)

    rows = [v.to_dict() for v in document.verified_values]
    if format == "json":
        return JSONResponse({"document": document.filename, "verified_values": rows})

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["field_name", "verified_value", "was_corrected", "verification_status"])
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r[k] for k in writer.fieldnames})
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={document.filename}_verified.csv"},
    )
