import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Extraction(Base):
    """A single AI-extracted field. Raw model output, never mutated after
    creation - corrections live in VerifiedValue instead so the original
    AI value is always preserved for audit purposes."""
    __tablename__ = "extractions"

    id = Column(String, primary_key=True, default=_uid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    field_name = Column(String, nullable=False)
    field_value = Column(Text, nullable=True)
    value_type = Column(String, default="string")  # string | number | date | currency
    # What KIND of information this is, independent of its data type above -
    # lets the UI group general-document knowledge (concepts, protocols,
    # algorithms, entities...) instead of only ever showing invoice-style
    # single fields. Additive column - existing rows default to "general".
    category = Column(String, default="general")
    confidence = Column(Float, default=0.0)
    source_location = Column(JSON, nullable=True)
    evidence_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    document = relationship("Document", back_populates="extractions")

    def to_dict(self):
        return {
            "id": self.id,
            "field_name": self.field_name,
            "field_value": self.field_value,
            "value_type": self.value_type,
            "category": self.category or "general",
            "confidence": self.confidence,
            "source_location": self.source_location,
            "evidence_text": self.evidence_text,
        }


class ValidationResult(Base):
    """Independent, non-LLM validation outcome. This is what keeps a
    high-confidence extraction from being blindly trusted."""
    __tablename__ = "validation_results"

    id = Column(String, primary_key=True, default=_uid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    rule_name = Column(String, nullable=False)  # e.g. "arithmetic_consistency"
    passed = Column(String, default="pass")  # pass | fail | warning
    message = Column(Text, nullable=True)
    fields_involved = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    document = relationship("Document", back_populates="validation_results")

    def to_dict(self):
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "passed": self.passed,
            "message": self.message,
            "fields_involved": self.fields_involved,
        }


class VerifiedValue(Base):
    """The single source of truth for a field once it has cleared review.
    RAG and exports must read from here, not from raw Extraction rows."""
    __tablename__ = "verified_values"

    id = Column(String, primary_key=True, default=_uid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    extraction_id = Column(String, ForeignKey("extractions.id"), nullable=True)
    field_name = Column(String, nullable=False)
    original_ai_value = Column(Text, nullable=True)
    verified_value = Column(Text, nullable=True)
    was_corrected = Column(String, default="no")  # yes | no
    verification_status = Column(String, default="verified")  # verified | rejected
    source_location = Column(JSON, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    document = relationship("Document", back_populates="verified_values")

    def to_dict(self):
        return {
            "id": self.id,
            "field_name": self.field_name,
            "original_ai_value": self.original_ai_value,
            "verified_value": self.verified_value,
            "was_corrected": self.was_corrected == "yes",
            "verification_status": self.verification_status,
            "source_location": self.source_location,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }