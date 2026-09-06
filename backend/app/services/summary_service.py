import json
import logging

from app.services.llm.factory import get_llm_provider

logger = logging.getLogger("veridoc.summary")

SUMMARY_SYSTEM = """TASK: SUMMARY
Summarize the document using only what is present in the text - do not add
outside information. Respond ONLY with JSON:
{"executive_summary": "2-4 sentences", "key_points": ["..."], "potential_issues": ["..."]}"""

SUGGESTIONS_SYSTEM = """TASK: SUGGESTIONS
Given the extracted fields below, write 3-5 short natural questions a user
would likely ask about this document. Respond ONLY with JSON:
{"questions": ["...", "..."]}"""


def generate_summary(document_text: str) -> dict:
    if not document_text.strip():
        return {"executive_summary": "No extractable text was found in this document.", "key_points": [], "potential_issues": []}
    provider = get_llm_provider()
    try:
        raw = provider.complete(SUMMARY_SYSTEM, f"DOCUMENT TEXT\n{document_text[:8000]}", json_mode=True)
        return json.loads(raw)
    except Exception as e:
        logger.warning("Summary generation failed: %s", e)
        return {"executive_summary": "Summary unavailable.", "key_points": [], "potential_issues": []}


def generate_suggested_questions(fields: list[dict]) -> list[str]:
    if not fields:
        return ["What is this document about?"]
    provider = get_llm_provider()
    try:
        raw = provider.complete(SUGGESTIONS_SYSTEM, f"FIELDS\n{json.dumps(fields)}", json_mode=True)
        data = json.loads(raw)
        return data.get("questions", [])[:6]
    except Exception as e:
        logger.warning("Suggested questions generation failed: %s", e)
        return [f"What is the {f['field_name'].lower()}?" for f in fields[:5]]


def compute_quality_score(has_text: bool, has_tables: bool, used_ocr: bool,
                           validation_failed: bool, avg_confidence: float,
                           missing_expected: bool) -> tuple[int, dict]:
    checks = {
        "text_extraction": has_text,
        "tables_detected": has_tables,
        "ocr_required": used_ocr,
        "validation_passed": not validation_failed,
        "sufficient_information": not missing_expected,
        "high_extraction_confidence": avg_confidence >= 0.75,
    }
    score = 40  # baseline for a document that processed at all
    score += 20 if has_text else 0
    score += 10 if has_tables else 0
    score += 0 if used_ocr else 10  # OCR pages are inherently a bit less certain
    score += 10 if not validation_failed else -10
    score += int(avg_confidence * 15)
    score += 5 if not missing_expected else -5
    return max(0, min(100, score)), checks
