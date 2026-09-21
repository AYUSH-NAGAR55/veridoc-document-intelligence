"""A deterministic, fully offline provider so VeriDoc is clickable end-to-end
without any API key. It uses regex heuristics instead of a real model, which
is honestly labeled everywhere in the UI as demo mode. It never invents
values - it only ever echoes text that is actually present in the prompt.

Important: this is a genuinely limited stand-in for a real LLM. It recognizes
"Label: Value" style lines and keyword overlap for retrieval - it cannot
understand meaning the way a real model can. For real extraction/answer
quality, set LLM_PROVIDER=openai (or ollama) with a working model. The filters
below exist to keep the *demo* honest by refusing to guess rather than
returning confident-looking garbage.
"""
import json
import re

from app.services.llm.base import LLMProvider

# A candidate field line must look like "Label: Value" where Label is a short,
# capitalized phrase (<=4 words) - this excludes most ordinary prose sentences
# that happen to contain a colon.
_KV_LINE = re.compile(r"^\s*([A-Z][A-Za-z0-9&/'.()]*(?:\s[A-Za-z0-9&/'.()]{1,20}){0,3})\s*:\s*(.+?)\s*$")
_CURRENCY = re.compile(r"(₹|\$|€|£)\s?[\d,]+(\.\d+)?\s?(crore|lakh|million|billion|cr)?", re.I)
_DATE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")

MIN_QUESTION_OVERLAP_RATIO = 0.34  # require ~1/3 of meaningful question words to be matched before answering


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

    # -- extraction: pull genuine "Label: Value" lines, rejecting anything that
    #    looks like ordinary prose (multi-sentence values, long labels, etc.) --
    def _extract(self, prompt: str) -> str:
        text = self._section(prompt, "DOCUMENT TEXT")
        fields = []
        seen_labels = set()
        for i, line in enumerate(text.splitlines()):
            m = _KV_LINE.match(line.strip())
            if not m:
                continue
            label, value = m.group(1).strip(), m.group(2).strip()
            if not self._is_plausible_field(label, value):
                continue
            key = label.lower()
            if key in seen_labels:
                continue  # keep the first occurrence only, avoid noisy duplicates
            seen_labels.add(key)

            value_type = "string"
            if _CURRENCY.search(value):
                value_type = "currency"
            elif _DATE.search(value):
                value_type = "date"
            elif re.match(r"^[\d,.]+$", value):
                value_type = "number"

            confidence = 0.88 if value_type in ("currency", "number", "date") else 0.72
            if len(value) < 2:
                confidence = 0.45

            fields.append({
                "field_name": label,
                "field_value": value,
                "value_type": value_type,
                "confidence": confidence,
                "source_location": {"line": i + 1},
                "evidence_text": line.strip()[:200],
            })

        kind = "financial_report" if any(_CURRENCY.search(f["field_value"]) for f in fields) else "general_document"
        return json.dumps({"document_kind": kind, "fields": fields[:25]})

    @staticmethod
    def _is_plausible_field(label: str, value: str) -> bool:
        if len(label.split()) > 4 or len(label) > 40:
            return False
        if not value or len(value) > 90:
            return False
        word_count = len(value.split())
        if word_count > 12:
            return False
        # More than one internal sentence break inside the value means this was
        # actually a paragraph, not a field - the regex matched a colon by accident.
        if value.count(". ") >= 1 and word_count > 6:
            return False
        if value.rstrip().endswith((".", "?", "!")) and word_count > 6:
            return False
        return True

    # -- RAG answer: find the retrieved chunk with the strongest keyword overlap,
    #    and only answer if that overlap clears a real relevance bar. Confidence
    #    scales with how much of the question was actually matched, instead of
    #    a fixed number - a weak match should not look as sure as a strong one. --
    def _answer(self, prompt: str) -> str:
        question = self._section(prompt, "QUESTION")
        context = self._section(prompt, "CONTEXT")
        q_words = {w.lower() for w in re.findall(r"\w+", question) if len(w) > 3}
        if not q_words:
            return json.dumps({"answer": None, "confidence": 0.0, "found": False})

        best_line, best_score = None, 0
        for line in context.splitlines():
            content = re.sub(r"^\[\d+\]\s*\([^)]*\)\s*", "", line)  # strip the "[1] (source label) " prefix
            words = {w.lower() for w in re.findall(r"\w+", content)}
            score = len(q_words & words)
            if score > best_score:
                best_score, best_line = score, content

        if not best_line or best_score == 0:
            return json.dumps({"answer": None, "confidence": 0.0, "found": False})

        overlap_ratio = best_score / len(q_words)
        if overlap_ratio < MIN_QUESTION_OVERLAP_RATIO:
            return json.dumps({"answer": None, "confidence": 0.0, "found": False})

        confidence = round(min(0.9, 0.35 + overlap_ratio * 0.55), 2)
        return json.dumps({"answer": best_line.strip()[:280], "confidence": confidence, "found": True})

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
        """Extracts the text between `marker` and whichever known marker comes
        next, so sections never bleed into each other (this previously caused
        the question's word set to accidentally include the context's words,
        producing false keyword matches)."""
        known_markers = ("QUESTION", "CONTEXT", "DOCUMENT TEXT", "TABLES", "FIELDS")
        idx = prompt.find(marker)
        if idx == -1:
            return prompt
        start = idx + len(marker)
        rest = prompt[start:]
        cut = len(rest)
        for m in known_markers:
            if m == marker:
                continue
            pos = rest.find(m)
            if pos != -1:
                cut = min(cut, pos)
        return rest[:cut].strip()
