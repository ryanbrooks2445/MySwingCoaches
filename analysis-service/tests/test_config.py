import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_missing_runtime_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("K_SERVICE", "myswingcoaches-analysis")

    with pytest.raises(ValidationError, match="Missing production settings"):
        Settings(_env_file=None)


def test_production_rejects_wildcard_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("K_SERVICE", "myswingcoaches-analysis")

    with pytest.raises(ValidationError, match="Wildcard CORS"):
        Settings(
            _env_file=None,
            supabase_url="https://example.supabase.co",
            supabase_service_role_key="service-key",
            gemini_api_key="gemini-key",
            analysis_service_secret="a-long-production-secret",
            allowed_cors_origins="*",
        )
