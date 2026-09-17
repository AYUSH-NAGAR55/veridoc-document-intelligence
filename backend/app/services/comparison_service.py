"""Compares verified values between two documents field-by-field. Deliberately
simple set-based diff rather than an LLM call, so results are deterministic
and explainable."""
import re

from app.models.document import Document

_NUM_RE = re.compile(r"[-+]?[\d,]+(?:\.\d+)?")


def _num(value: str) -> float | None:
    m = _NUM_RE.search((value or "").replace(",", ""))
    return float(m.group().replace(",", "")) if m else None


def compare_documents(doc_a: Document, doc_b: Document) -> dict:
    values_a = {v.field_name.strip().lower(): v for v in doc_a.verified_values if v.verification_status == "verified"}
    values_b = {v.field_name.strip().lower(): v for v in doc_b.verified_values if v.verification_status == "verified"}

    all_keys = set(values_a) | set(values_b)
    changed, added, removed, unchanged = [], [], [], []

    for key in sorted(all_keys):
        a, b = values_a.get(key), values_b.get(key)
        if a and not b:
            removed.append({"field_name": a.field_name, "value_a": a.verified_value, "value_b": None})
        elif b and not a:
            added.append({"field_name": b.field_name, "value_a": None, "value_b": b.verified_value})
        elif a.verified_value == b.verified_value:
            unchanged.append({"field_name": a.field_name, "value": a.verified_value})
        else:
            na, nb = _num(a.verified_value), _num(b.verified_value)
            pct_change = None
            if na is not None and nb is not None and na != 0:
                pct_change = round(((nb - na) / abs(na)) * 100, 1)
            changed.append({
                "field_name": a.field_name,
                "value_a": a.verified_value,
                "value_b": b.verified_value,
                "percent_change": pct_change,
            })

    return {
        "document_a": {"id": doc_a.id, "filename": doc_a.filename},
        "document_b": {"id": doc_b.id, "filename": doc_b.filename},
        "changed": changed,
        "added": added,
        "removed": removed,
        "unchanged": unchanged,
    }
