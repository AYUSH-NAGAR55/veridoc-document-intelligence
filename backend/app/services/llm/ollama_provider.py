import httpx

from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Talks to a locally running Ollama server (https://ollama.com) via its
    /api/chat endpoint. Used for local/self-hosted extraction and RAG answers
    with no external API or key required.

    Requires Ollama to be installed and running (`ollama serve`, usually
    started automatically), with the configured model already pulled
    (`ollama pull <model>`). If Ollama is unreachable, `complete()` raises -
    callers (extraction_service, rag_service) already catch this and degrade
    to an empty/"not found" result rather than crashing the app.
    """

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return f"ollama:{self.model}"

    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        if json_mode:
            # Ollama's structured-output mode: constrains the model to emit valid JSON.
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"Could not reach Ollama at {self.base_url}. Is it running? Start it with `ollama serve` "
                f"and make sure the model is pulled: `ollama pull {self.model}`."
            ) from e
