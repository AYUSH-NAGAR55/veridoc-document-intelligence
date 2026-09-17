import httpx

from app.services.llm.base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Works with OpenAI itself, and any OpenAI-compatible endpoint
    (Azure OpenAI, OpenRouter, Together, vLLM, etc.) via LLM_API_BASE."""

    def __init__(self, api_key: str, api_base: str, model: str):
        if not api_key:
            raise ValueError(
                "LLM_PROVIDER is 'openai' but LLM_API_KEY is empty. "
                "Set it in your .env, or switch LLM_PROVIDER to 'mock' for offline demo mode."
            )
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model

    @property
    def name(self) -> str:
        return f"openai:{self.model}"

    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
