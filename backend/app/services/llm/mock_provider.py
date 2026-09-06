"""A deterministic, fully offline provider so VeriDoc is clickable end-to-end
without any API key. It uses simple regex heuristics instead of a real model,
which is honestly labeled everywhere in the UI as demo mode. It never invents
values - it only ever echoes text that is actually present in the prompt."""
import json
import re

from app.services.llm.base import LLMProvider

_KV_LINE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /_-]{2,40}?)\s*[:\-]\s*(.+?)\s*$")
_CURRENCY = re.compile(r"(₹|\$|€|£)\s?[\d,]+(\.\d+)?\s?(crore|lakh|million|billion|cr)?", re.I)
_DATE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")


class MockProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "mock (offline demo)"

    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        if "TASK: EXTRACTION" in system_prompt:
            return self._extract(user_prompt)
        if "TASK: RAG_ANSWER" in system_prompt:
            return self._answer(user_prompt)
        if "TASK: SUMMARY" in system_prompt:
            return self._summary(user_prompt)
        if "TASK: SUGGESTIONS" in system_prompt:
            return self._suggestions(user_prompt)
        return json.dumps({}) if json_mode else ""

    # -- extraction: pull "Label: Value" style lines out of the document text --
    def _extract(self, prompt: str) -> str:
        text = self._section(prompt, "DOCUMENT TEXT")
        fields = []
        for i, line in enumerate(text.splitlines()):
            m = _KV_LINE.match(line)
            if not m:
                continue
            label, value = m.group(1).strip(), m.group(2).strip()
            if len(value) > 120 or not value:
                continue
            value_type = "string"
            if _CURRENCY.search(value):
                value_type = "currency"
            elif _DATE.search(value):
                value_type = "date"
            elif re.match(r"^[\d,.]+$", value):
                value_type = "number"
            confidence = 0.9 if value_type in ("currency", "number", "date") else 0.8
            if len(value) < 2:
                confidence = 0.5
            fields.append({
                "field_name": label,
                "field_value": value,
                "value_type": value_type,
                "confidence": confidence,
                "source_location": {"line": i + 1},
                "evidence_text": line.strip(),
            })
        kind = "financial_report" if any(_CURRENCY.search(f["field_value"]) for f in fields) else "general_document"
        return json.dumps({"document_kind": kind, "fields": fields[:40]})

    # -- RAG answer: find the retrieved chunk with the most keyword overlap --
    def _answer(self, prompt: str) -> str:
        question = self._section(prompt, "QUESTION")
        context = self._section(prompt, "CONTEXT")
        q_words = {w.lower() for w in re.findall(r"\w+", question) if len(w) > 3}
        best_line, best_score = None, 0
        for line in context.splitlines():
            words = {w.lower() for w in re.findall(r"\w+", line)}
            score = len(q_words & words)
            if score > best_score:
                best_score, best_line = score, line
        if not best_line or best_score == 0:
            return json.dumps({"answer": None, "confidence": 0.0, "found": False})
        return json.dumps({"answer": best_line.strip(), "confidence": 0.75, "found": True})

    def _summary(self, prompt: str) -> str:
        text = self._section(prompt, "DOCUMENT TEXT")
        lines = [l.strip() for l in text.splitlines() if l.strip()][:5]
        return json.dumps({
            "executive_summary": " ".join(lines)[:400] or "Not enough extractable text to summarize.",
            "key_points": lines[:5],
            "potential_issues": [],
        })

    def _suggestions(self, prompt: str) -> str:
        text = self._section(prompt, "FIELDS")
        names = re.findall(r'"field_name":\s*"([^"]+)"', text)
        qs = [f"What is the {n.lower()}?" for n in names[:5]]
        return json.dumps({"questions": qs or ["What is this document about?"]})

    @staticmethod
    def _section(prompt: str, marker: str) -> str:
        idx = prompt.find(marker)
        if idx == -1:
            return prompt
        return prompt[idx + len(marker):]
