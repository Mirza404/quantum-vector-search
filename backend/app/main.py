"""FastAPI application factory."""

from fastapi import FastAPI

from .api import api_router

APP_NAME = "Quantum Vector Search API"
APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.include_router(api_router)
    return app


app = create_app()
