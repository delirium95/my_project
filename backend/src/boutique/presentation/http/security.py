from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from boutique.application.auth.interfaces import GetCurrentUserUseCase
from boutique.domain.auth.exceptions import AuthenticationError, InvalidTokenError
from boutique.domain.auth.interfaces import TokenService
from boutique.domain.users.models import User

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


@inject
async def get_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    token_service: Annotated[TokenService, Depends(Provide["token_service"])],
    get_current_user: Annotated[GetCurrentUserUseCase, Depends(Provide["get_current_user"])],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        user_id = token_service.decode_access(token=credentials.credentials)
        return await get_current_user(user_id=str(user_id))
    except (AuthenticationError, InvalidTokenError):
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from None
