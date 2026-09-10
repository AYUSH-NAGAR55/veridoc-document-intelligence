"""Turns raw document text/tables into structured, confidence-scored fields
using the configured LLM, and validates every response against a strict
Pydantic schema so malformed model output can never crash the pipeline or
silently corrupt the database."""
import json
import logging

from pydantic import ValidationError

from app.schemas.schemas import CATEGORY_VALUES, ExtractedField, ExtractionOutput
from app.services.llm.factory import get_llm_provider

logger = logging.getLogger("veridoc.extraction")

SYSTEM_PROMPT = """TASK: EXTRACTION
You are a precise document extraction engine. Extract only information that is
explicitly present in the provided document text. Never infer, guess, or
fabricate a value, a page number, or evidence. If you are not confident a
field is correct, give it a low confidence score rather than omitting it or
making it up. Distinguish a fact explicitly stated in the document from
something you would have to infer - only extract the former.

Extract structured knowledge from the document, not just invoice-style single
fields. Depending on what the document actually contains, look for:
- document_metadata: title, document type, subject/domain, author(s), organization, date
- key_concept: important concepts/ideas the document explains
- technology_protocol_tool: named technologies, protocols, tools, standards, languages
- algorithm_method: named algorithms, methods, or techniques described
- entity: important named people, organizations, products, or systems
- numerical_value: specific percentages, measurements, dates, quantities, statistics actually stated
- relationship: an explicit comparison or relationship between two things the document states (e.g. "Broadcast -> all devices")
- table_data: a meaningful fact drawn from a table in the document

Only include a category if the document actually contains that kind of
information - do not force items into categories that don't apply. If the
document contains no useful structured information at all, return an empty
"fields" list rather than inventing anything.

IMPORTANT: "field_name" must be the SPECIFIC name of the thing you extracted
(e.g. "Broadcast Routing", "OSPF", "Reverse Path Forwarding", "Author"), never
a generic category label like "Key Concept" repeated across items - every
field_name should be unique and specific to what it names. "field_value"
holds the definition/description/value for that specific item, using the
document's own wording where possible.

Respond ONLY with a single JSON object shaped exactly like this:
{
  "document_kind": "invoice | financial_report | research_paper | technical_presentation | manual | contract | general_document | ...",
  "fields": [
    {
      "field_name": "string - the specific name of the item (not a category label)",
      "field_value": "string - its value/definition/description",
      "value_type": "string | number | date | currency",
      "category": "document_metadata | key_concept | technology_protocol_tool | algorithm_method | entity | numerical_value | relationship | table_data | general",
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
    logger.info("Extraction request via %s (document_text=%d chars, tables=%d chars)",
                provider.name, len(document_text), len(tables_summary))

    try:
        raw = provider.complete(SYSTEM_PROMPT, user_prompt, json_mode=True)
    except Exception as e:  # LLM/network failure
        logger.error("LLM extraction call failed: %s", e)
        return ExtractionOutput(document_kind="general_document", fields=[])

    logger.info("Extraction raw response (%d chars): %s", len(raw), raw[:3000])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Extraction response was not valid JSON, returning empty result: %s", e)
        return ExtractionOutput(document_kind="general_document", fields=[])

    if not isinstance(data, dict):
        logger.warning("Extraction response was valid JSON but not an object, returning empty result.")
        return ExtractionOutput(document_kind="general_document", fields=[])

    document_kind = data.get("document_kind") or "general_document"
    raw_fields = data.get("fields")
    if not isinstance(raw_fields, list):
        logger.warning("Extraction response had no usable 'fields' list, returning empty result.")
        return ExtractionOutput(document_kind=document_kind, fields=[])

    # IMPORTANT: validate each field independently instead of the whole list
    # at once. A single malformed item (e.g. a category value the model
    # invented that isn't one of the allowed ones) used to fail
    # ExtractionOutput.model_validate() for the ENTIRE batch, silently
    # discarding every other correctly-extracted field along with it. Now one
    # bad item is dropped and logged, and every valid item still survives.
    valid_fields: list[ExtractedField] = []
    dropped = 0
    for item in raw_fields:
        if not isinstance(item, dict):
            dropped += 1
            continue
        item = dict(item)
        if item.get("category") not in CATEGORY_VALUES:
            item["category"] = "general"  # small local models often invent/typo enum values
        try:
            valid_fields.append(ExtractedField.model_validate(item))
        except ValidationError as e:
            dropped += 1
            logger.warning("Dropped one malformed extracted field (%r): %s", item.get("field_name"), e)

    logger.info("Extraction result: kept %d field(s), dropped %d malformed field(s).", len(valid_fields), dropped)
    return ExtractionOutput(document_kind=document_kind, fields=valid_fields)