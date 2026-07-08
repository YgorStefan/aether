import os

import structlog
from fastapi import FastAPI

from api.middleware.cors import add_cors_middleware
from api.middleware.rate_limit import add_rate_limit_middleware
from api.routes import account, admin, health, runs, settings as settings_route, skills
from core.config import settings
from core.logging import configure_logging

logger = structlog.get_logger()

_REQUIRED_FOR_PRODUCTION = ["supabase_url", "supabase_service_key", "gemini_api_key"]
_API_V1_PREFIX = "/api/v1"


def _warn_missing_config() -> None:
    missing = [name for name in _REQUIRED_FOR_PRODUCTION if not getattr(settings, name)]
    if missing:
        logger.warning("missing_config", missing=missing, detail="app iniciando sem envs críticas")
    if not settings.settings_encryption_key:
        logger.warning("settings_encryption_key_not_set", detail="API keys de usuário serão salvas em texto puro")


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    _warn_missing_config()

    if settings.langsmith_api_key:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)

    app = FastAPI(title="Aether API", version="1.0.0")
    add_cors_middleware(app)
    add_rate_limit_middleware(app)
    app.include_router(health.router, prefix=_API_V1_PREFIX)
    app.include_router(runs.router, prefix=_API_V1_PREFIX)
    app.include_router(skills.router, prefix=_API_V1_PREFIX)
    app.include_router(settings_route.router, prefix=_API_V1_PREFIX)
    app.include_router(admin.router, prefix=_API_V1_PREFIX)
    app.include_router(account.router, prefix=_API_V1_PREFIX)

    if settings.mcp_api_key:
        from api.routes.mcp import get_mcp_asgi_app
        app.mount("/mcp", get_mcp_asgi_app())

    return app


app = create_app()
