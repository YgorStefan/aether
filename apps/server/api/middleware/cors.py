from fastapi.middleware.cors import CORSMiddleware
from core.config import settings


def add_cors_middleware(app) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url] + settings.extra_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
