from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    gemini_api_key: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "aether-os"

    frontend_url: str = "http://localhost:3000"
    default_budget_limit: int = 10000
    max_requests_per_minute: int = 20
    log_level: str = "INFO"


settings = Settings()
