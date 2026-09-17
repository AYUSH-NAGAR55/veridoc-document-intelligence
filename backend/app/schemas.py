import datetime

from pydantic import BaseModel


class LocationOut(BaseModel):
    page: int | None = None
    section: str | None = None
    paragraph: int | None = None
    sheet: str | None = None
    row: int | None = None
    column: str | None = None
    table: str | None = None
    image: str | None = None
    region: list[float] | None = None
    line: int | None = None

    class Config:
        from_attributes = True


class ContentUnitOut(BaseModel):
    unit_index: int
    content_type: str
    location: LocationOut
    ocr_confidence: float | None = None
    extraction_notes: str = ""
    preview: str = ""

    class Config:
        from_attributes = True


class AuditEntryOut(BaseModel):
    action: str
    previous_value: str | None
    new_value: str | None
    reviewer_note: str | None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class FieldOut(BaseModel):
    id: str
    document_id: str
    field_name: str
    field_value: str
    original_ai_value: str | None = None
    confidence: float
    location: LocationOut
    source_snippet: str = ""
    status: str
    is_verified: bool
    validation_notes: list[dict] = []
    audit_entries: list[AuditEntryOut] = []

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    doc_type: str
    status: str
    unit_count: int
    unit_count_label: str
    summary: str = ""
    size_bytes: int = 0
    error_message: str | None = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class DocumentDetailOut(DocumentOut):
    content_units: list[ContentUnitOut] = []
    fields: list[FieldOut] = []


class CorrectFieldIn(BaseModel):
    corrected_value: str


class RejectFieldIn(BaseModel):
    reason: str | None = None


class BulkDeleteIn(BaseModel):
    document_ids: list[str]


class AskIn(BaseModel):
    question: str


class SourceOut(BaseModel):
    location: LocationOut
    text: str
    score: float


class AskOut(BaseModel):
    answer: str
    found: bool
    confidence: float
    sources: list[SourceOut] = []


class DashboardOut(BaseModel):
    total_documents: int
    processing_documents: int
    ready_documents: int
    needs_review_documents: int
    failed_documents: int
    total_fields: int
    verified_fields: int
    pending_review_fields: int
    indexed_vectors: int
    recent_documents: list[DocumentOut]
    recent_reviews: list[AuditEntryOut]
