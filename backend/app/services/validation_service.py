"""Independent, deterministic Python validation. This layer never looks at
the LLM's self-reported confidence - it only checks whether extracted values
are internally consistent, plausible, and complete. A high-confidence
extraction can still fail every rule here."""
import re
from dataclasses import dataclass
from datetime import datetime

_NUMERIC_RE = re.compile(r"[-+]?[\d,]+(?:\.\d+)?")

# Common field-name aliases so "Grand Total" and "Total" are recognised as the same concept.
SUBTOTAL_KEYS = {"subtotal", "sub total", "sub-total", "net amount"}
TAX_KEYS = {"tax", "gst", "vat", "sales tax"}
TOTAL_KEYS = {"total", "grand total", "amount due", "total amount"}


@dataclass
class ValidationOutcome:
    rule_name: str
    passed: str  # pass | fail | warning
    message: str
    fields_involved: list[str]


def _to_number(value: str) -> float | None:
    if not value:
        return None
    match = _NUMERIC_RE.search(value.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group().replace(",", ""))
    except ValueError:
        return None


def _find_field(fields: list[dict], keys: set[str]) -> dict | None:
    for f in fields:
        if f["field_name"].strip().lower() in keys:
            return f
    return None


def run_validations(fields: list[dict]) -> list[ValidationOutcome]:
    """`fields` is a list of dicts with field_name/field_value/value_type/confidence."""
    outcomes: list[ValidationOutcome] = []
    outcomes.extend(_check_arithmetic_consistency(fields))
    outcomes.extend(_check_missing_required_fields(fields))
    outcomes.extend(_check_dates(fields))
    outcomes.extend(_check_impossible_numbers(fields))
    outcomes.extend(_check_duplicates(fields))
    if not outcomes:
        outcomes.append(ValidationOutcome(
            rule_name="general", passed="pass", message="No issues detected.", fields_involved=[],
        ))
    return outcomes


def _check_arithmetic_consistency(fields: list[dict]) -> list[ValidationOutcome]:
    subtotal = _find_field(fields, SUBTOTAL_KEYS)
    tax = _find_field(fields, TAX_KEYS)
    total = _find_field(fields, TOTAL_KEYS)
    if not (subtotal and total):
        return []

    sub_n = _to_number(subtotal["field_value"])
    tax_n = _to_number(tax["field_value"]) if tax else 0.0
    total_n = _to_number(total["field_value"])
    if sub_n is None or total_n is None:
        return []

    expected = round(sub_n + (tax_n or 0.0), 2)
    actual = round(total_n, 2)
    involved = [subtotal["field_name"], total["field_name"]] + ([tax["field_name"]] if tax else [])

    if abs(expected - actual) < 0.5:
        return [ValidationOutcome(
            rule_name="arithmetic_consistency", passed="pass",
            message=f"Subtotal + tax ({expected}) matches total ({actual}).",
            fields_involved=involved,
        )]
    return [ValidationOutcome(
        rule_name="arithmetic_consistency", passed="fail",
        message=f"Subtotal + tax = {expected}, but total = {actual}. Values are inconsistent.",
        fields_involved=involved,
    )]


def _check_missing_required_fields(fields: list[dict]) -> list[ValidationOutcome]:
    names = {f["field_name"].strip().lower() for f in fields}
    if any(k in names for k in TOTAL_KEYS) and not any(k in names for k in SUBTOTAL_KEYS):
        return [ValidationOutcome(
            rule_name="missing_field", passed="warning",
            message="A total was found but no subtotal - arithmetic consistency cannot be fully verified.",
            fields_involved=["Subtotal"],
        )]
    return []


def _check_dates(fields: list[dict]) -> list[ValidationOutcome]:
    outcomes = []
    for f in fields:
        if f.get("value_type") != "date":
            continue
        value = f["field_value"]
        parsed = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%B %d, %Y", "%d %B %Y"):
            try:
                parsed = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            outcomes.append(ValidationOutcome(
                rule_name="invalid_date", passed="warning",
                message=f"'{value}' for {f['field_name']} could not be parsed as a valid date.",
                fields_involved=[f["field_name"]],
            ))
        elif parsed.year < 1970 or parsed.year > datetime.now().year + 1:
            outcomes.append(ValidationOutcome(
                rule_name="implausible_date", passed="fail",
                message=f"{f['field_name']} = '{value}' is outside a plausible date range.",
                fields_involved=[f["field_name"]],
            ))
    return outcomes


def _check_impossible_numbers(fields: list[dict]) -> list[ValidationOutcome]:
    outcomes = []
    for f in fields:
        if f.get("value_type") not in ("number", "currency"):
            continue
        n = _to_number(f["field_value"])
        if n is None:
            continue
        if n < 0 and f["field_name"].strip().lower() in (TOTAL_KEYS | SUBTOTAL_KEYS | TAX_KEYS):
            outcomes.append(ValidationOutcome(
                rule_name="impossible_value", passed="fail",
                message=f"{f['field_name']} is negative ({f['field_value']}), which is not plausible.",
                fields_involved=[f["field_name"]],
            ))
        if abs(n) > 10**12:
            outcomes.append(ValidationOutcome(
                rule_name="implausible_magnitude", passed="warning",
                message=f"{f['field_name']} = {f['field_value']} is unusually large - please confirm.",
                fields_involved=[f["field_name"]],
            ))
    return outcomes


def _check_duplicates(fields: list[dict]) -> list[ValidationOutcome]:
    seen: dict[str, str] = {}
    outcomes = []
    for f in fields:
        key = f["field_name"].strip().lower()
        if key in seen and seen[key] != f["field_value"]:
            outcomes.append(ValidationOutcome(
                rule_name="conflicting_extraction", passed="fail",
                message=f"'{f['field_name']}' was extracted with two different values: "
                        f"'{seen[key]}' and '{f['field_value']}'.",
                fields_involved=[f["field_name"]],
            ))
        seen[key] = f["field_value"]
    return outcomes
