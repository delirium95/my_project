from uuid import uuid4

import pytest

from boutique.domain.auth.exceptions import InvalidTokenError
from boutique.domain.auth.interfaces import RefreshTokenBlacklist
from boutique.domain.ids import UserID
from boutique.infrastructure.auth.jwt_token_service import JwtTokenService


class FakeRefreshTokenBlacklist(RefreshTokenBlacklist):
    def __init__(self) -> None:
        self.revoked: set[str] = set()

    async def consume(self, *, token_id: str, ttl_seconds: int) -> bool:
        if token_id in self.revoked:
            return False
        self.revoked.add(token_id)
        return True

    async def revoke(self, *, token_id: str, ttl_seconds: int) -> None:
        self.revoked.add(token_id)


@pytest.mark.unit
async def test_jwt_service_rotates_refresh_token_and_rejects_reuse() -> None:
    service = JwtTokenService(
        blacklist=FakeRefreshTokenBlacklist(),
        secret="test-secret-that-is-at-least-thirty-two-bytes-long",
        access_ttl_minutes=15,
        refresh_ttl_days=7,
    )
    user_id = UserID(uuid4())
    tokens = service.issue(user_id=user_id)

    assert service.decode_access(token=tokens.access_token) == user_id
    rotated = await service.rotate_refresh(refresh_token=tokens.refresh_token)

    assert rotated.access_token != tokens.access_token
    assert rotated.refresh_token != tokens.refresh_token
    with pytest.raises(InvalidTokenError):
        await service.rotate_refresh(refresh_token=tokens.refresh_token)
