import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import get_settings
from app.core.exceptions import VeriDocError
from app.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("veridoc")

settings = get_settings()

app = FastAPI(
    title="VeriDoc API",
    description="Verified Document Intelligence & Source-Grounded RAG Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("VeriDoc backend started (provider=%s, db=%s)", settings.llm_provider, settings.database_url)


@app.exception_handler(VeriDocError)
def handle_veridoc_error(request: Request, exc: VeriDocError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our end. Please try again."})


app.include_router(api_router)
