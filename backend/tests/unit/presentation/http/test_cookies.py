from fastapi import Response

from boutique.presentation.http.cookies import clear_refresh_token_cookie, set_refresh_token_cookie


def test_cross_site_refresh_cookie_is_secure_and_http_only() -> None:
    response = Response()

    set_refresh_token_cookie(
        response,
        refresh_token="token",
        max_age_seconds=60,
        secure=True,
        samesite="none",
    )

    header = response.headers["set-cookie"]
    assert "HttpOnly" in header
    assert "SameSite=none" in header
    assert "Secure" in header


def test_clear_refresh_cookie_uses_the_same_cookie_attributes() -> None:
    response = Response()

    clear_refresh_token_cookie(response, secure=True, samesite="none")

    header = response.headers["set-cookie"]
    assert "SameSite=none" in header
    assert "Secure" in header
