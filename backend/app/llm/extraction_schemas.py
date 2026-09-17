"""Pydantic models the LLM's JSON output is validated against.

Ollama is asked to return JSON matching this shape. If it returns
something malformed, Pydantic's validation error tells us exactly what's
wrong, which `llm_extractor.py` uses to decide whether to retry once
with a corrective follow-up prompt or give up gracefully.
"""
from pydantic import BaseModel, Field, field_validator


class ExtractedFieldLLM(BaseModel):
    field: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_location: dict = Field(default_factory=dict)
    evidence: str = ""

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return 0.3
        return max(0.0, min(1.0, v))


class LLMExtractionResult(BaseModel):
    document_type: str = "generic"
    summary: str = ""
    fields: list[ExtractedFieldLLM] = Field(default_factory=list)
