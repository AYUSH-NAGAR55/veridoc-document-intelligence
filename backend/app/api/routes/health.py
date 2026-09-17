from fastapi import APIRouter

from app.config import get_settings
from app.services.llm.factory import get_llm_provider

router = APIRouter(tags=["health"])


@router.get("/")
def root():
    return {"service": "VeriDoc API", "status": "running"}


@router.get("/health")
def health():
    settings = get_settings()
    provider = get_llm_provider()
    return {
        "status": "ok",
        "environment": settings.environment,
        "llm_provider": provider.name,
        "database": settings.database_url.split("://")[0],
    }
