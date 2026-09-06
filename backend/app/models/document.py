import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship

from app.database import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    UNDERSTANDING = "understanding"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    VERIFYING = "verifying"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    IMAGE = "image"


class Document(Base):
    """The normalized document record. One row per uploaded file, regardless
    of its underlying format - format-specific detail lives in ContentUnit."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uid)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    file_type = Column(Enum(DocumentType), nullable=False)
    content_type = Column(String, nullable=True)
    size_bytes = Column(Integer, default=0)
    file_hash = Column(String, index=True, nullable=True)

    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.UPLOADED)
    status_message = Column(String, nullable=True)

    document_kind = Column(String, nullable=True)  # e.g. "invoice", "financial_report" (inferred, not hard-coded)
    quality_score = Column(Integer, nullable=True)  # 0-100
    quality_checks = Column(JSON, nullable=True)

    summary = Column(JSON, nullable=True)
    suggested_questions = Column(JSON, nullable=True)
    pii_findings = Column(JSON, nullable=True)

    used_ocr = Column(Integer, default=0)  # boolean-ish for cross-db portability
    duplicate_of = Column(String, ForeignKey("documents.id"), nullable=True)
    duplicate_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    content_units = relationship("ContentUnit", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="document", cascade="all, delete-orphan")
    review_items = relationship("ReviewItem", back_populates="document", cascade="all, delete-orphan")
    verified_values = relationship("VerifiedValue", back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type.value if self.file_type else None,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "status": self.status.value if self.status else None,
            "status_message": self.status_message,
            "document_kind": self.document_kind,
            "quality_score": self.quality_score,
            "quality_checks": self.quality_checks,
            "summary": self.summary,
            "suggested_questions": self.suggested_questions,
            "pii_findings": self.pii_findings,
            "used_ocr": bool(self.used_ocr),
            "duplicate_of": self.duplicate_of,
            "duplicate_score": self.duplicate_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ContentUnit(Base):
    """A unit of extracted content with format-appropriate provenance.

    `location` is a small JSON blob whose shape depends on file_type, e.g.:
      PDF  -> {"page": 3}
      DOCX -> {"section": "Financial Summary", "paragraph": 12}
      CSV  -> {"sheet": "Sheet1", "row": 4, "column": "Revenue"}
      TXT  -> {"line": 22}
      IMAGE-> {"region": [x, y, w, h]}
    """
    __tablename__ = "content_units"

    id = Column(String, primary_key=True, default=_uid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    content_type = Column(String, default="text")  # text | table | image_text
    text = Column(Text, nullable=True)
    table_data = Column(JSON, nullable=True)  # {"headers": [...], "rows": [[...]]}
    location = Column(JSON, nullable=True)
    unit_metadata = Column(JSON, nullable=True)
    order_index = Column(Integer, default=0)

    document = relationship("Document", back_populates="content_units")

    def to_dict(self):
        return {
            "id": self.id,
            "content_type": self.content_type,
            "text": self.text,
            "table_data": self.table_data,
            "location": self.location,
            "metadata": self.unit_metadata,
            "order_index": self.order_index,
        }


class Chunk(Base):
    """A retrieval unit for RAG. Chunks are built only from verified/validated
    content and carry the source location forward so answers can cite it."""
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=_uid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    content_unit_id = Column(String, ForeignKey("content_units.id"), nullable=True)
    text = Column(Text, nullable=False)
    location = Column(JSON, nullable=True)
    vector_index = Column(Integer, nullable=True)  # position inside the FAISS index
    source_label = Column(String, nullable=True)  # human readable e.g. "Page 17 - Financial Summary"

    document = relationship("Document", back_populates="chunks")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "location": self.location,
            "source_label": self.source_label,
        }
