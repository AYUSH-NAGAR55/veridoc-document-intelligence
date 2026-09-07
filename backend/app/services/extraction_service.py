"""Turns raw document text/tables into structured, confidence-scored fields
using the configured LLM, and validates every response against a strict
Pydantic schema so malformed model output can never crash the pipeline or
silently corrupt the database."""
import json
import logging

from pydantic import ValidationError

from app.schemas.schemas import ExtractionOutput
from app.services.llm.factory import get_llm_provider

logger = logging.getLogger("veridoc.extraction")

SYSTEM_PROMPT = """TASK: EXTRACTION
You are a precise document extraction engine. Extract only information that is
explicitly present in the provided document text. Never infer, guess, or
fabricate a value. If you are not confident a field is correct, give it a low
confidence score rather than omitting it or making it up.

Respond ONLY with a single JSON object shaped exactly like this:
{
  "document_kind": "invoice | financial_report | research_paper | contract | general_document | ...",
  "fields": [
    {
      "field_name": "string",
      "field_value": "string",
      "value_type": "string | number | date | currency",
      "confidence": 0.0-1.0,
      "source_location": {"page": 1},
      "evidence_text": "the exact sentence/line the value came from"
    }
  ]
}
No text outside the JSON object."""


def extract_fields(document_text: str, tables_summary: str = "") -> ExtractionOutput:
    if not document_text.strip() and not tables_summary.strip():
        return ExtractionOutput(document_kind="general_document", fields=[])

    provider = get_llm_provider()
    user_prompt = (
        f"DOCUMENT TEXT\n{document_text[:12000]}\n\n"
        f"TABLES\n{tables_summary[:4000]}"
    )

    try:
        raw = provider.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
        data = json.loads(raw)
        return ExtractionOutput.model_validate(data)
    except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as e:
        logger.warning("Extraction output failed validation, returning empty result: %s", e)
        return ExtractionOutput(document_kind="general_document", fields=[])
    except Exception as e:  # LLM/network failure
        logger.error("LLM extraction call failed: %s", e)
        return ExtractionOutput(document_kind="general_document", fields=[])
