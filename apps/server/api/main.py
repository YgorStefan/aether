from fastapi import FastAPI

from api.middleware.cors import add_cors_middleware
from api.middleware.rate_limit import add_rate_limit_middleware
from api.routes import health, runs
from core.config import settings
from core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title="Aether OS API", version="1.0.0")
    add_cors_middleware(app)
    add_rate_limit_middleware(app)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(runs.router, prefix="/api/v1")

    return app


app = create_app()
