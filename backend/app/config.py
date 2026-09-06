"""Central application configuration, sourced entirely from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "VeriDoc"
    environment: str = "development"
    secret_key: str = "dev-secret-change-me"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    database_url: str = "sqlite:///./storage/veridoc.db"

    upload_dir: str = "./storage/uploads"
    index_dir: str = "./storage/index"
    max_upload_size_mb: int = 25

    llm_provider: str = "mock"  # openai | ollama | mock
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    ocr_engine: str = "tesseract"
    tesseract_cmd: str = ""

    confidence_auto_accept_threshold: float = 0.70

    analytics_id: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
