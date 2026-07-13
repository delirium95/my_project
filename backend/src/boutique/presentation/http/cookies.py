from typing import Literal

from fastapi import Response

_REFRESH_TOKEN_COOKIE = "refresh_token"


def set_refresh_token_cookie(
    response: Response,
    *,
    refresh_token: str,
    max_age_seconds: int,
    secure: bool,
    samesite: Literal["lax", "strict", "none"],
) -> None:
    response.set_cookie(
        key=_REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/api/v1/auth",
    )


def clear_refresh_token_cookie(
    response: Response,
    *,
    secure: bool,
    samesite: Literal["lax", "strict", "none"],
) -> None:
    response.delete_cookie(
        key=_REFRESH_TOKEN_COOKIE,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/api/v1/auth",
    )
