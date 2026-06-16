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
