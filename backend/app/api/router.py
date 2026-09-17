from fastapi import APIRouter

from app.api.routes import health, documents, review, query, compare, analytics

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(review.router)
api_router.include_router(query.router)
api_router.include_router(compare.router)
api_router.include_router(analytics.router)
