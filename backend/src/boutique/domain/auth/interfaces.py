from abc import ABC, abstractmethod

from boutique.domain.auth.models import TokenPair
from boutique.domain.ids import UserID


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, *, password: str) -> str:
        """Return a one-way password hash."""

    @abstractmethod
    def verify(self, *, password: str, password_hash: str) -> None:
        """Raise ``InvalidCredentialsError`` when the password does not match."""


class RefreshTokenBlacklist(ABC):
    @abstractmethod
    async def consume(self, *, token_id: str, ttl_seconds: int) -> bool:
        """Atomically mark a token as used and return whether it was unused."""

    @abstractmethod
    async def revoke(self, *, token_id: str, ttl_seconds: int) -> None:
        """Record a revoked refresh-token ID until it naturally expires."""


class TokenService(ABC):
    @abstractmethod
    def issue(self, *, user_id: UserID) -> TokenPair:
        """Issue a signed access and refresh token pair."""

    @abstractmethod
    def decode_access(self, *, token: str) -> UserID:
        """Verify an access token and return its typed subject."""

    @abstractmethod
    async def rotate_refresh(self, *, refresh_token: str) -> TokenPair:
        """Consume a refresh token and issue a new pair."""

    @abstractmethod
    async def revoke_refresh(self, *, refresh_token: str) -> None:
        """Invalidate a refresh token for logout."""
