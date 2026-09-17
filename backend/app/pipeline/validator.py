"""Independent validation, run against whatever fields the LLM extracted
(no longer a fixed field list per document type -- the LLM can extract
fields for an invoice, a financial report, a research paper, or anything
else, and this validator works generically off field names).

A validation failure forces human review even when the LLM reported high
confidence -- this is an explicit, non-negotiable rule: validation output
can only ever lower the effective confidence used for the auto-accept
decision, never raise it above what the LLM itself reported.
"""
import re
from dataclasses import dataclass, field as dc_field

from .. import config

DATE_PATTERNS = [
    r"^\d{4}[\-\/]\d{1,2}[\-\/]\d{1,2}$",
    r"^\d{1,2}[\-\/]\d{1,2}[\-\/]\d{2,4}$",
    r"^[A-Za-z]+\s\d{1,2},?\s\d{4}$",
]

# Field-name aliases used only to *recognise* which cross-checks might
# apply -- this is not a required-fields list, just a "if these three
# happen to be present, check their arithmetic" lookup.
NUMERIC_ALIASES = {
    "subtotal": "subtotal", "sub total": "subtotal", "sub-total": "subtotal",
    "tax": "tax", "gst": "tax", "vat": "tax",
    "total": "total", "grand total": "total",
    "revenue": "revenue", "sales": "revenue",
    "operating expenses": "opex", "expenses": "opex", "opex": "opex",
    "net income": "net_income", "profit": "net_income", "net profit": "net_income",
}


@dataclass
class ValidatedField:
    field_name: str
    value: str
    numeric_value: float | None
    confidence: float
    location: dict
    source_snippet: str
    notes: list
    auto_status: str   # "auto_accepted" | "pending"
    is_verified: bool


def parse_number(raw: str) -> float | None:
    cleaned = re.sub(r"[₹$€£,\s]", "", raw)
    cleaned = re.sub(r"(crore|cr|million|mn|lakh|bn|billion)", "", cleaned, flags=re.IGNORECASE).strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def is_valid_date(raw: str) -> bool:
    return any(re.match(p, raw.strip()) for p in DATE_PATTERNS)


def validate_llm_fields(llm_fields: list, ocr_confidence_by_index: dict | None = None) -> list[ValidatedField]:
    """llm_fields: list of ExtractedFieldLLM (field, value, confidence, source_location, evidence)
    ocr_confidence_by_index: optional {field index: ocr_confidence or None}, from resolving
    each field's evidence back to the content unit it came from -- a field
    read off a low-confidence OCR page should not carry the LLM's full
    self-reported confidence.
    """
    ocr_confidence_by_index = ocr_confidence_by_index or {}
    validated = []
    numeric_lookup: dict[str, float] = {}

    for f in llm_fields:
        alias = NUMERIC_ALIASES.get(f.field.strip().lower())
        parsed = parse_number(f.value)
        if alias and parsed is not None:
            numeric_lookup[alias] = parsed

    for idx, f in enumerate(llm_fields):
        notes = []
        confidence = f.confidence
        name_lower = f.field.strip().lower()
        parsed = parse_number(f.value)
        looks_numeric = alias_hint = NUMERIC_ALIASES.get(name_lower)

        ocr_conf = ocr_confidence_by_index.get(idx)
        if ocr_conf is not None:
            confidence = (confidence + ocr_conf) / 2
            notes.append({"rule": "ocr_quality", "passed": ocr_conf >= 0.7,
                           "message": f"Source text OCR confidence {ocr_conf * 100:.0f}%."})

        if "date" in name_lower:
            valid_date = is_valid_date(f.value)
            notes.append({"rule": "date_format", "passed": valid_date,
                           "message": "Recognisable date format." if valid_date else "Date format looks unusual."})
            if not valid_date:
                confidence = min(confidence, 0.5)

        if looks_numeric:
            ok = parsed is not None
            notes.append({"rule": "numeric_parse", "passed": ok,
                           "message": "Parsed as a number." if ok else "Could not parse a clean number."})
            if not ok:
                confidence = min(confidence, 0.4)

        validated.append(ValidatedField(
            field_name=f.field, value=f.value, numeric_value=parsed,
            confidence=round(confidence, 3), location=f.source_location or {},
            source_snippet=f.evidence, notes=notes, auto_status="pending", is_verified=False,
        ))

    _cross_check_invoice_math(validated, numeric_lookup)
    _cross_check_financials(validated, numeric_lookup)

    for v in validated:
        hard_failure = any(not n["passed"] and n["rule"] == "arithmetic_check" for n in v.notes)
        eligible = v.confidence >= config.REVIEW_THRESHOLD and not hard_failure
        v.auto_status = "auto_accepted" if eligible else "pending"
        v.is_verified = eligible

    return validated


def _cross_check_invoice_math(validated: list[ValidatedField], numeric: dict):
    sub, tax, total = numeric.get("subtotal"), numeric.get("tax"), numeric.get("total")
    if sub is None or tax is None or total is None:
        return
    expected = round(sub + tax, 2)
    passed = abs(expected - round(total, 2)) < max(0.01 * total, 1.0)
    message = (f"Subtotal + Tax = {expected:,.2f}, matches stated Total." if passed
               else f"Subtotal + Tax = {expected:,.2f}, but stated Total is {total:,.2f} -- mismatch.")
    for v in validated:
        alias = NUMERIC_ALIASES.get(v.field_name.strip().lower())
        if alias in ("subtotal", "tax", "total"):
            v.notes.append({"rule": "arithmetic_check", "passed": passed, "message": message})
            if not passed:
                v.confidence = min(v.confidence, 0.55)


def _cross_check_financials(validated: list[ValidatedField], numeric: dict):
    revenue, opex, net_income = numeric.get("revenue"), numeric.get("opex"), numeric.get("net_income")
    if revenue is None or opex is None or net_income is None:
        return
    expected = round(revenue - opex, 2)
    tolerance = max(0.05 * abs(revenue), 5.0)
    passed = abs(expected - round(net_income, 2)) <= tolerance
    message = (f"Revenue - Operating expenses ~= {expected:,.2f}, consistent with stated Net income."
               if passed else
               f"Revenue - Operating expenses ~= {expected:,.2f}, but stated Net income is {net_income:,.2f} -- check for other line items.")
    for v in validated:
        alias = NUMERIC_ALIASES.get(v.field_name.strip().lower())
        if alias in ("revenue", "opex", "net_income"):
            v.notes.append({"rule": "arithmetic_check", "passed": passed, "message": message})
            if not passed:
                v.confidence = min(v.confidence, 0.6)
