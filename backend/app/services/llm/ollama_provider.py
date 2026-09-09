import httpx

from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Local development only - do not point production at this."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return f"ollama:{self.model}"

    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        # Local CPU inference is much slower than a hosted API, and structured
        # extraction prompts (full document text + a large JSON schema to
        # fill in) are a far bigger generation task than a short RAG answer.
        # 120s was enough for Q&A but was cutting off extraction mid-generation
        # on this hardware ("timed out"), silently producing zero extracted
        # fields even though nothing about the prompt/parsing was wrong.
        with httpx.Client(timeout=600.0) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")