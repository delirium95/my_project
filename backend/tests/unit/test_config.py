import pytest
from pydantic import ValidationError

from boutique.config import Settings


@pytest.mark.unit
def test_production_settings_reject_insecure_authentication_defaults() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(
            environment="production",
            jwt_secret="local-development-only-change-me",
            cookie_secure=True,
        )

    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(
            environment="production",
            jwt_secret="production-secret-that-is-long-and-unique",
            cookie_secure=False,
        )


@pytest.mark.unit
def test_production_settings_accept_secure_authentication_configuration() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="production-secret-that-is-long-and-unique",
        cookie_secure=True,
    )

    assert settings.cookie_secure is True


@pytest.mark.unit
def test_production_settings_accept_cross_site_secure_cookie_configuration() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="production-secret-that-is-long-and-unique",
        cookie_secure=True,
        cookie_samesite="none",
    )

    assert settings.cookie_samesite == "none"
