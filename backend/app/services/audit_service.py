from sqlalchemy.orm import Session

from app.models.review import AuditLog


def log(db: Session, document_id: str, action: str, field_name: str | None = None,
        before_value: str | None = None, after_value: str | None = None,
        actor: str = "system", reason: str | None = None):
    entry = AuditLog(
        document_id=document_id, action=action, field_name=field_name,
        before_value=before_value, after_value=after_value, actor=actor, reason=reason,
    )
    db.add(entry)
    db.commit()
    return entry
