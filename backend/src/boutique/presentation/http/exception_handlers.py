from fastapi import Request, status
from fastapi.responses import JSONResponse

from boutique.domain.auth.exceptions import (
    AuthenticationError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    RefreshTokenStoreUnavailableError,
)


async def authentication_error_handler(
    _: Request,
    error: AuthenticationError,
) -> JSONResponse:
    if isinstance(error, EmailAlreadyRegisteredError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(error)},
        )
    if isinstance(error, (InvalidCredentialsError, InvalidTokenError)):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(error)},
        )
    if isinstance(error, RefreshTokenStoreUnavailableError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(error)},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(error)},
    )
