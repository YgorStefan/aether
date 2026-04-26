from fastapi import FastAPI
from core.config import settings
from core.logging import configure_logging
from api.middleware.cors import add_cors_middleware
from api.routes import health


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title="Aether OS API", version="1.0.0")
    add_cors_middleware(app)
    app.include_router(health.router, prefix="/api/v1")

    return app


app = create_app()
