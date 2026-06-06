from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    gemini_api_key: str = ""
    analysis_service_secret: str = "change-me-in-production"
    allowed_cors_origins: str = ""
    # Pro is the highest-accuracy default for paid swing analysis; Flash is fallback.
    gemini_model: str = "gemini-2.5-pro"
    gemini_fallback_model: str = "gemini-2.5-flash"
    sam3_enabled: bool = True
    sam3_model: str = "mobile_sam.pt"
    sam3_max_frames: int = 6
    sam3_confidence: float = 0.25


def get_settings() -> Settings:
    return Settings()
