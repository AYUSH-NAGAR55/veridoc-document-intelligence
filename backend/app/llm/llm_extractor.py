"""LLM structured extraction (Step 4, real version — not regex).

Builds a grounding prompt that explicitly forbids inventing values,
sends it to Ollama, and validates the JSON response against
`LLMExtractionResult`. On a malformed response, retries once with the
validation error fed back to the model. If Ollama is unreachable at
all, raises `OllamaUnavailable` so the orchestrator can mark the
document as failed with a clear, actionable message instead of crashing.
"""
import json

from pydantic import ValidationError

from .ollama_client import generate_json, OllamaUnavailable, OllamaMalformedResponse
from .extraction_schemas import LLMExtractionResult

SYSTEM_PROMPT = """You are a careful document-extraction assistant.

Rules you must always follow:
- Only extract information that is explicitly present in the document text given to you.
- NEVER invent, guess, or infer a value that is not directly stated.
- If a field is not present, omit it entirely rather than guessing.
- Assign a low confidence (below 0.5) to anything you are not sure about.
- Always return your best guess at which type of document this is (e.g. "invoice", "financial_report", "research_paper", "contract", "generic").
- Respond with ONLY a single JSON object, no other text, matching exactly this shape:

{
  "document_type": "invoice",
  "summary": "one sentence describing what this document is",
  "fields": [
    {"field": "Vendor", "value": "Acme Supplies", "confidence": 0.95, "evidence": "the exact text span you based this on"}
  ]
}
"""


def extract_fields(document_text: str, retry_feedback: str | None = None) -> LLMExtractionResult:
    """Raises OllamaUnavailable if the server can't be reached.
    Raises OllamaMalformedResponse if the retry also fails validation.
    """
    prompt = f"Document text:\n\"\"\"\n{document_text[:6000]}\n\"\"\"\n\nExtract the structured fields now."
    if retry_feedback:
        prompt += f"\n\nYour previous response was invalid: {retry_feedback}\nReturn ONLY corrected JSON matching the required shape."

    raw = generate_json(prompt, system=SYSTEM_PROMPT)  # may raise OllamaUnavailable

    try:
        return LLMExtractionResult.model_validate(raw)
    except ValidationError as exc:
        if retry_feedback is not None:
            # Already retried once — give up cleanly.
            raise OllamaMalformedResponse(f"Ollama's response didn't match the expected shape after a retry: {exc}") from exc
        return extract_fields(document_text, retry_feedback=str(exc)[:500])
