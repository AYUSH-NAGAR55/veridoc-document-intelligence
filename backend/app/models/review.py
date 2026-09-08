import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ReviewItem(Base):
    """A queued human-review task, created when confidence is low or
    validation fails. Never silently resolved by the system."""
    __tablename__ = "review_items"

    id = Column(String, primary_key=True, default=_uid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    extraction_id = Column(String, ForeignKey("extractions.id"), nullable=True)

    field_name = Column(String, nullable=False)
    ai_value = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    source_location = Column(JSON, nullable=True)
    evidence_text = Column(Text, nullable=True)

    reason = Column(String, nullable=False)  # low_confidence | validation_failure | both
    validation_message = Column(Text, nullable=True)

    status = Column(String, default="pending")  # pending | accepted | corrected | rejected
    corrected_value = Column(Text, nullable=True)
    reviewer_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_now)

    document = relationship("Document", back_populates="review_items")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "field_name": self.field_name,
            "ai_value": self.ai_value,
            "confidence": self.confidence,
            "source_location": self.source_location,
            "evidence_text": self.evidence_text,
            "reason": self.reason,
            "validation_message": self.validation_message,
            "status": self.status,
            "corrected_value": self.corrected_value,
            "reviewer_note": self.reviewer_note,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    """Append-only history of anything that changed trusted knowledge."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=_uid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    field_name = Column(String, nullable=True)
    action = Column(String, nullable=False)  # extracted | corrected | accepted | rejected | verified | deleted
    actor = Column(String, default="system")  # system | reviewer
    before_value = Column(Text, nullable=True)
    after_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    document = relationship("Document", back_populates="audit_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "field_name": self.field_name,
            "action": self.action,
            "actor": self.actor,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
