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

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")
