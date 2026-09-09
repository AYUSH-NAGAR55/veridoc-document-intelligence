import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, JSON, Text

from app.database import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class QueryLog(Base):
    """History of RAG questions asked, for analytics and the 'recent activity' feed."""
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=_uid)
    owner_id = Column(String, index=True, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    document_ids = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    grounded = Column(String, default="yes")  # yes | no (no = "could not find" response)
    created_at = Column(DateTime(timezone=True), default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "document_ids": self.document_ids,
            "sources": self.sources,
            "confidence": self.confidence,
            "grounded": self.grounded == "yes",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
