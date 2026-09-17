"""SQLAlchemy models for VeriDoc.

A Document goes through: uploaded -> understanding -> extracting ->
validating -> verifying -> indexing -> ready (or needs_review while
some fields are still pending human attention).

Migration note (from the original PDF-only schema): `Page.page_number`
and `ExtractedField.source_page` (plain ints) have been replaced with a
generic `location` JSON column everywhere, storing whichever of
page/section/paragraph/sheet/row/column/table/image/region/line applies
to that document's format. This is a schema change, not a data
migration -- since this is a local SQLite file used for development/demo,
existing rows aren't converted; delete `veridoc.db` and it'll be
recreated with the new shape on next startup.
"""
import datetime
import enum
import uuid

from sqlalchemy import (Column, String, Integer, Float, Text, DateTime,
                         ForeignKey, Enum, JSON, Boolean)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class DocStatus(str, enum.Enum):
    uploaded = "uploaded"
    understanding = "understanding"
    extracting = "extracting"
    validating = "validating"
    verifying = "verifying"
    indexing = "indexing"
    ready = "ready"
    needs_review = "needs_review"
    failed = "failed"


class ContentUnit(Base):
    """One retrievable slice of a document -- a PDF page, a DOCX paragraph,
    a CSV row/column, a JSON leaf, a whole image. Replaces the old
    PDF-only `Page` model.
    """
    __tablename__ = "content_units"

    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("documents.id"))
    unit_index = Column(Integer, nullable=False)
    content_type = Column(String, default="text")
    location = Column(JSON, default=dict)
    raw_text = Column(Text, default="")
    tables_json = Column(JSON, default=list)
    ocr_confidence = Column(Float, nullable=True)
    extraction_notes = Column(Text, default="")

    document = relationship("Document", back_populates="content_units")


class ExtractedField(Base):
    """A single structured field pulled out of the document, e.g. 'Tax': 26100.

    Keeps AI extraction and human-verified value permanently separate --
    `field_value` is whatever is currently considered correct (starts as
    the AI value, becomes the corrected value after review), while
    `original_ai_value` never changes once set, so a full audit trail is
    always reconstructable even without the ReviewAudit rows.
    """
    __tablename__ = "extracted_fields"

    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("documents.id"))
    field_name = Column(String, nullable=False)
    field_value = Column(String, nullable=False)
    original_ai_value = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    location = Column(JSON, default=dict)
    source_snippet = Column(Text, default="")
    status = Column(String, default="pending")  # pending / accepted / corrected / rejected / auto_accepted
    is_verified = Column(Boolean, default=False)
    validation_notes = Column(JSON, default=list)
    corrected_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="fields")
    audit_entries = relationship("ReviewAudit", back_populates="field", cascade="all, delete-orphan")


class ReviewAudit(Base):
    """Immutable log of every human review decision on a field -- accept,
    reject, or correct. Never overwritten; new decisions append new rows.
    """
    __tablename__ = "review_audit"

    id = Column(String, primary_key=True, default=gen_id)
    field_id = Column(String, ForeignKey("extracted_fields.id"))
    action = Column(String, nullable=False)   # accept | reject | correct
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    reviewer_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    field = relationship("ExtractedField", back_populates="audit_entries")


class Chunk(Base):
    """A retrievable slice of verified document content, embedded and
    indexed in FAISS for RAG.
    """
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=gen_id)
    document_id = Column(String, ForeignKey("documents.id"))
    location = Column(JSON, default=dict)
    text = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=True)

    document = relationship("Document", back_populates="chunks")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_id)
    filename = Column(String, nullable=False)
    file_type = Column(String, default="unknown")
    doc_type = Column(String, default="unknown")
    status = Column(Enum(DocStatus), default=DocStatus.uploaded)
    unit_count = Column(Integer, default=0)
    unit_count_label = Column(String, default="pages")
    summary = Column(Text, default="")
    size_bytes = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                         onupdate=datetime.datetime.utcnow)

    content_units = relationship("ContentUnit", back_populates="document", cascade="all, delete-orphan")
    fields = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
