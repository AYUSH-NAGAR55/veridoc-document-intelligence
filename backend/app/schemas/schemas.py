"""Pydantic schemas: API request/response shapes, and the strict schema the
LLM's structured extraction output is validated against."""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# LLM structured extraction output (this is what protects us from bad AI output)
# ---------------------------------------------------------------------------

class ExtractedField(BaseModel):
    field_name: str
    field_value: str
    value_type: Literal["string", "number", "date", "currency"] = "string"
    confidence: float = Field(ge=0.0, le=1.0)
    source_location: dict = Field(default_factory=dict)
    evidence_text: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v):
        return max(0.0, min(1.0, v))


class ExtractionOutput(BaseModel):
    """The full shape we require from the LLM. If the model returns anything
    that doesn't fit this, we fall back to an empty result rather than crash."""
    document_kind: str = "general_document"
    fields: list[ExtractedField] = Field(default_factory=list)


class TableRelationship(BaseModel):
    row_label: str
    values: dict[str, str]


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    id: str
    filename: str
    status: str


class ReviewActionRequest(BaseModel):
    reviewer_note: Optional[str] = None


class ReviewCorrectionRequest(BaseModel):
    corrected_value: str
    reviewer_note: Optional[str] = None


class QueryRequest(BaseModel):
    question: str
    document_ids: Optional[list[str]] = None  # None = search across all ready documents
    top_k: int = 5


class CompareRequest(BaseModel):
    document_id_a: str
    document_id_b: str
