"""Grounded RAG (Steps 9-10, real version).

Question -> embed -> FAISS retrieval (scoped to the document, preferring
verified chunks) -> grounded prompt (retrieved text only, explicitly
told not to use outside knowledge) -> Ollama -> answer + sources +
evidence + confidence.

If retrieval finds nothing relevant, or Ollama is unreachable, this
returns an honest "not found" / error answer rather than ever falling
back to an ungrounded guess.
"""
import json
from dataclasses import dataclass

from ..embeddings import embedding_model, vector_index
from ..llm.ollama_client import generate_json, OllamaUnavailable

SIMILARITY_FLOOR = 0.35   # below this, we don't trust the retrieval enough to answer

SYSTEM_PROMPT = """You answer questions using ONLY the evidence provided to you below.

Rules:
- Do not use any knowledge you have outside of the provided evidence.
- If the evidence does not contain the answer, say so plainly -- do not guess or infer.
- Keep the answer to one or two sentences.
- Respond with ONLY a JSON object of this shape:
{"answer": "...", "found": true, "confidence": 0.9}
"found" must be false if the evidence doesn't actually answer the question.
"confidence" should reflect how directly the evidence supports the answer.
"""


@dataclass
class Answer:
    text: str
    sources: list[dict]     # [{location, text, score}]
    confidence: float
    found: bool


def answer_question(document_id: str, question: str) -> Answer:
    try:
        query_vector = embedding_model.embed([question])[0]
    except Exception as exc:
        return Answer(
            text=f"Search isn't available right now (embedding model couldn't load: {exc}).",
            sources=[], confidence=0.0, found=False,
        )

    hits = vector_index.search(query_vector, k=5, document_id=document_id)
    relevant_hits = [h for h in hits if h["score"] >= SIMILARITY_FLOOR]

    if not relevant_hits:
        return Answer(
            text="The requested information could not be found in the verified document knowledge.",
            sources=[], confidence=0.0, found=False,
        )

    evidence_block = "\n\n".join(
        f"[{i + 1}] {h['text']}" for i, h in enumerate(relevant_hits)
    )
    prompt = f"Question: {question}\n\nEvidence:\n{evidence_block}\n\nAnswer using only this evidence."

    try:
        raw = generate_json(prompt, system=SYSTEM_PROMPT)
    except OllamaUnavailable as exc:
        # Retrieval worked, but we can't synthesize an answer without the
        # LLM -- surface the strongest retrieved passage directly rather
        # than fail completely, and say plainly that composition failed.
        top = relevant_hits[0]
        return Answer(
            text=f"(Ollama unavailable to compose an answer -- showing the most relevant passage found instead.) {top['text']}",
            sources=[{"location": h["location"], "text": h["text"], "score": h["score"]} for h in relevant_hits],
            confidence=round(top["score"], 3),
            found=True,
        )

    found = bool(raw.get("found", True))
    if not found:
        return Answer(
            text="The requested information could not be found in the verified document knowledge.",
            sources=[], confidence=0.0, found=False,
        )

    return Answer(
        text=str(raw.get("answer", "")).strip(),
        sources=[{"location": h["location"], "text": h["text"], "score": h["score"]} for h in relevant_hits],
        confidence=round(float(raw.get("confidence", relevant_hits[0]["score"])), 3),
        found=True,
    )
