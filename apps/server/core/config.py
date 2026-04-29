from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    gemini_api_key: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "aether-os"

    tavily_api_key: str = ""
    e2b_api_key: str = ""

    frontend_url: str = "http://localhost:3000"
    extra_cors_origins: list[str] = []

    @field_validator("extra_cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: object) -> list[str]:
        if isinstance(v, list):
            return v
        if not v or not str(v).strip():
            return []
        import json
        try:
            return json.loads(str(v))
        except Exception:
            return [s.strip() for s in str(v).split(",") if s.strip()]
    default_budget_limit: int = 10000
    max_requests_per_minute: int = 20
    log_level: str = "INFO"

    memory_similarity_threshold: float = 0.7  # limiar para busca cosine no pgvector
    mcp_api_key: str = ""                      # se vazio, MCP Server não é montado


settings = Settings()
