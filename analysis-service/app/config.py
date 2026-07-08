import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    gemini_api_key: str = ""
    analysis_service_secret: str = "change-me-in-production"
    allowed_cors_origins: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_model: str = "gemini-2.5-flash"
    gemini_max_quality_revisions: int = 3
    gemini_max_output_tokens: int = 12000
    gemini_temperature: float = 0.25
    gemini_top_p: float = 0.9
    sentry_dsn: str = ""

    @model_validator(mode="after")
    def validate_runtime(self):
        is_production = os.getenv("ENVIRONMENT") == "production" or bool(os.getenv("K_SERVICE"))
        if not is_production:
            return self

        required = {
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
            "GEMINI_API_KEY": self.gemini_api_key,
            "ANALYSIS_SERVICE_SECRET": self.analysis_service_secret,
            "ALLOWED_CORS_ORIGINS": self.allowed_cors_origins,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"Missing production settings: {', '.join(missing)}")
        if self.analysis_service_secret == "change-me-in-production":
            raise ValueError("ANALYSIS_SERVICE_SECRET must be changed in production")
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS is not allowed in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        if not self.allowed_cors_origins.strip():
            return ["*"]
        return [
            origin.strip().rstrip("/")
            for origin in self.allowed_cors_origins.split(",")
            if origin.strip()
        ]


def get_settings() -> Settings:
    return Settings()
