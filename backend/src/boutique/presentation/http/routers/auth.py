from typing import Annotated, Literal

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, Response, status

from boutique.application.auth.interfaces import (
    LoginUseCase,
    LogoutUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
)
from boutique.domain.auth.exceptions import InvalidTokenError
from boutique.domain.auth.models import LoginInput, RegisterUserInput
from boutique.domain.users.models import User
from boutique.presentation.http.cookies import clear_refresh_token_cookie, set_refresh_token_cookie
from boutique.presentation.http.schemas.auth import (
    AccessTokenResponseSchema,
    LoginRequestSchema,
    RegisterUserRequestSchema,
    UserResponseSchema,
)
from boutique.presentation.http.security import get_authenticated_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
@inject
async def register_user(
    payload: RegisterUserRequestSchema,
    use_case: Annotated[RegisterUserUseCase, Depends(Provide["register_user"])],
) -> UserResponseSchema:
    user = await use_case(
        input_data=RegisterUserInput(
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
        )
    )
    return _user_response(user=user)


@router.post("/login", response_model=AccessTokenResponseSchema)
@inject
async def login(
    response: Response,
    payload: LoginRequestSchema,
    use_case: Annotated[LoginUseCase, Depends(Provide["login"])],
    cookie_secure: Annotated[bool, Depends(Provide["config.cookie_secure"])],
    cookie_samesite: Annotated[
        Literal["lax", "strict", "none"], Depends(Provide["config.cookie_samesite"])
    ],
    refresh_ttl_days: Annotated[int, Depends(Provide["config.jwt_refresh_ttl_days"])],
) -> AccessTokenResponseSchema:
    tokens = await use_case(
        input_data=LoginInput(email=str(payload.email), password=payload.password)
    )
    set_refresh_token_cookie(
        response,
        refresh_token=tokens.refresh_token,
        max_age_seconds=refresh_ttl_days * 24 * 60 * 60,
        secure=cookie_secure,
        samesite=cookie_samesite,
    )
    return AccessTokenResponseSchema(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in_seconds=tokens.expires_in_seconds,
    )


@router.post("/refresh", response_model=AccessTokenResponseSchema)
@inject
async def refresh(
    response: Response,
    use_case: Annotated[RefreshTokenUseCase, Depends(Provide["refresh_token"])],
    cookie_secure: Annotated[bool, Depends(Provide["config.cookie_secure"])],
    cookie_samesite: Annotated[
        Literal["lax", "strict", "none"], Depends(Provide["config.cookie_samesite"])
    ],
    refresh_ttl_days: Annotated[int, Depends(Provide["config.jwt_refresh_ttl_days"])],
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> AccessTokenResponseSchema:
    if refresh_token is None:
        raise InvalidTokenError("Refresh token is required")
    tokens = await use_case(refresh_token=refresh_token)
    set_refresh_token_cookie(
        response,
        refresh_token=tokens.refresh_token,
        max_age_seconds=refresh_ttl_days * 24 * 60 * 60,
        secure=cookie_secure,
        samesite=cookie_samesite,
    )
    return AccessTokenResponseSchema(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in_seconds=tokens.expires_in_seconds,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def logout(
    response: Response,
    use_case: Annotated[LogoutUseCase, Depends(Provide["logout"])],
    cookie_secure: Annotated[bool, Depends(Provide["config.cookie_secure"])],
    cookie_samesite: Annotated[
        Literal["lax", "strict", "none"], Depends(Provide["config.cookie_samesite"])
    ],
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> Response:
    if refresh_token is not None:
        await use_case(refresh_token=refresh_token)
        clear_refresh_token_cookie(
            response,
            secure=cookie_secure,
            samesite=cookie_samesite,
        )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponseSchema)
async def get_current_user(
    user: Annotated[User, Depends(get_authenticated_user)],
) -> UserResponseSchema:
    return _user_response(user=user)


def _user_response(*, user: User) -> UserResponseSchema:
    return UserResponseSchema(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
    )
