from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Every provider just needs to turn a prompt into text. Keeping this
    interface tiny is what lets VeriDoc swap OpenAI / Ollama / a mock without
    touching extraction or RAG logic."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
