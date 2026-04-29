import os

from fastapi import FastAPI

from api.middleware.cors import add_cors_middleware
from api.middleware.rate_limit import add_rate_limit_middleware
from api.routes import health, runs, settings as settings_route, skills
from core.config import settings
from core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    if settings.langsmith_api_key:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)

    app = FastAPI(title="Aether API", version="1.0.0")
    add_cors_middleware(app)
    add_rate_limit_middleware(app)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(runs.router, prefix="/api/v1")
    app.include_router(skills.router, prefix="/api/v1")
    app.include_router(settings_route.router, prefix="/api/v1")

    if settings.mcp_api_key:
        from api.routes.mcp import get_mcp_asgi_app
        app.mount("/mcp", get_mcp_asgi_app())

    return app


app = create_app()
