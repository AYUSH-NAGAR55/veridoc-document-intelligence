import re

PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"),
    "account_number": re.compile(r"\b\d{9,18}\b"),
    "pan_or_id": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),  # e.g. Indian PAN-style ID
}


def detect_pii(text: str) -> list[dict]:
    findings = []
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text or ""):
            findings.append({"type": kind, "value": match.group(), "position": match.start()})
    return findings


def mask(text: str) -> str:
    masked = text
    for kind, pattern in PATTERNS.items():
        masked = pattern.sub(lambda m: "•" * len(m.group()), masked)
    return masked
