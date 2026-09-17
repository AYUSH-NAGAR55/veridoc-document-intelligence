from functools import lru_cache

from app.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.openai_provider import OpenAICompatibleProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.mock_provider import MockProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "openai":
        if not settings.llm_api_key:
            # Fail soft into demo mode rather than making the whole app unusable
            # because a key hasn't been configured yet.
            return MockProvider()
        return OpenAICompatibleProvider(settings.llm_api_key, settings.llm_api_base, settings.llm_model)

    if provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)

    return MockProvider()
