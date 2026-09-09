from functools import lru_cache

from app.config import get_settings
from app.core.exceptions import VeriDocError
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
            # IMPORTANT: this used to fail *soft* into MockProvider here, which
            # meant a misconfigured deployment would silently answer every
            # question with MockProvider's bare keyword/heading-overlap logic
            # while everyone believed OpenAI was generating the answers. That
            # is a config error, not a legitimate offline mode, so it must be
            # loud and specific instead of invisible. Explicit offline demo
            # mode is still available and unaffected: set LLM_PROVIDER=mock.
            raise VeriDocError(
                "LLM_PROVIDER is set to 'openai' but LLM_API_KEY is empty, so no "
                "real model can be called. Set LLM_API_KEY in the backend .env, "
                "or set LLM_PROVIDER=mock to intentionally run in offline demo mode.",
                status_code=500,
            )
        return OpenAICompatibleProvider(settings.llm_api_key, settings.llm_api_base, settings.llm_model)

    if provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)

    return MockProvider()