from abc import ABC, abstractmethod

from boutique.domain.auth.models import LoginInput, RegisterUserInput, TokenPair
from boutique.domain.users.models import User


class RegisterUserUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, input_data: RegisterUserInput) -> User:
        """Create a local user account."""


class LoginUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, input_data: LoginInput) -> TokenPair:
        """Validate credentials and issue an access token."""


class RefreshTokenUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, refresh_token: str) -> TokenPair:
        """Rotate one valid refresh token."""


class LogoutUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, refresh_token: str) -> None:
        """Invalidate a refresh token if it is valid."""


class GetCurrentUserUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, user_id: str) -> User:
        """Resolve the authenticated user by their stable application ID."""
