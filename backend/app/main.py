"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router

APP_NAME = "Quantum Vector Search API"
APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite dev server
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
