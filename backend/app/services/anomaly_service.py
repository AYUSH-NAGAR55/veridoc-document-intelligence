"""Lightweight statistical anomaly detection across similar documents.
Flags things as warnings for a human to consider - never asserts fraud."""
import re
import statistics

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.extraction import Extraction

_NUM_RE = re.compile(r"[-+]?[\d,]+(?:\.\d+)?")


def _num(value: str) -> float | None:
    m = _NUM_RE.search((value or "").replace(",", ""))
    return float(m.group().replace(",", "")) if m else None


def detect_anomalies(db: Session, document: Document, owner_id: str) -> list[dict]:
    if not document.document_kind:
        return []

    peers = db.query(Document).filter(
        Document.document_kind == document.document_kind,
        Document.id != document.id,
        Document.status == "ready",
        Document.owner_id == owner_id,
    ).limit(30).all()
    if len(peers) < 3:
        return []

    findings = []
    my_fields = {e.field_name.strip().lower(): e for e in document.extractions}

    for field_name, my_extraction in my_fields.items():
        my_value = _num(my_extraction.field_value)
        if my_value is None:
            continue
        peer_values = []
        for peer in peers:
            for e in peer.extractions:
                if e.field_name.strip().lower() == field_name:
                    v = _num(e.field_value)
                    if v is not None:
                        peer_values.append(v)
        if len(peer_values) < 3:
            continue
        mean = statistics.mean(peer_values)
        stdev = statistics.pstdev(peer_values) or 1.0
        z = (my_value - mean) / stdev
        if abs(z) >= 2.5:
            findings.append({
                "field_name": my_extraction.field_name,
                "value": my_extraction.field_value,
                "peer_average": round(mean, 2),
                "deviation": round(z, 2),
                "message": f"{my_extraction.field_name} ({my_value}) is unusually "
                           f"{'high' if z > 0 else 'low'} compared to similar documents "
                           f"(average {round(mean, 2)}).",
            })
    return findings
