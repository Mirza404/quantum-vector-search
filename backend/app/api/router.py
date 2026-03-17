"""Top-level API router for FastAPI."""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api")

# Future routers (e.g., search endpoints) should be included here, e.g.
# api_router.include_router(search.router, prefix="/search", tags=["search"])
