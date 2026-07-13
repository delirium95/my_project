import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Final
from uuid import UUID

import jwt

from boutique.domain.auth.exceptions import InvalidTokenError
from boutique.domain.auth.interfaces import RefreshTokenBlacklist, TokenService
from boutique.domain.auth.models import TokenPair
from boutique.domain.ids import UserID

_ACCESS: Final = "access"
_REFRESH: Final = "refresh"


class JwtTokenService(TokenService):
    def __init__(
        self,
        *,
        blacklist: RefreshTokenBlacklist,
        secret: str,
        access_ttl_minutes: int,
        refresh_ttl_days: int,
    ) -> None:
        self._blacklist = blacklist
        self._secret = secret
        self._access_ttl = timedelta(minutes=access_ttl_minutes)
        self._refresh_ttl = timedelta(days=refresh_ttl_days)

    def issue(self, *, user_id: UserID) -> TokenPair:
        return TokenPair(
            access_token=self._encode(
                claims={"sub": str(user_id), "type": _ACCESS, "jti": secrets.token_urlsafe(24)},
                ttl=self._access_ttl,
            ),
            refresh_token=self._encode(
                claims={"sub": str(user_id), "type": _REFRESH, "jti": secrets.token_urlsafe(24)},
                ttl=self._refresh_ttl,
            ),
            expires_in_seconds=int(self._access_ttl.total_seconds()),
        )

    def decode_access(self, *, token: str) -> UserID:
        claims = self._decode(token=token, expected_type=_ACCESS)
        return self._parse_subject(claims=claims)

    async def rotate_refresh(self, *, refresh_token: str) -> TokenPair:
        claims = self._decode(token=refresh_token, expected_type=_REFRESH)
        token_id = self._parse_token_id(claims=claims)
        remaining_lifetime = self._remaining_lifetime_seconds(claims=claims)
        if not await self._blacklist.consume(
            token_id=token_id,
            ttl_seconds=remaining_lifetime,
        ):
            raise InvalidTokenError("Invalid or expired refresh token")
        return self.issue(user_id=self._parse_subject(claims=claims))

    async def revoke_refresh(self, *, refresh_token: str) -> None:
        try:
            claims = self._decode(token=refresh_token, expected_type=_REFRESH)
            await self._blacklist.revoke(
                token_id=self._parse_token_id(claims=claims),
                ttl_seconds=self._remaining_lifetime_seconds(claims=claims),
            )
        except InvalidTokenError:
            return

    def _encode(self, *, claims: dict[str, str], ttl: timedelta) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            payload={**claims, "iat": now, "exp": now + ttl},
            key=self._secret,
            algorithm="HS256",
        )

    def _decode(self, *, token: str, expected_type: str) -> dict[str, Any]:
        try:
            claims = jwt.decode(jwt=token, key=self._secret, algorithms=["HS256"])
        except jwt.PyJWTError as error:
            raise InvalidTokenError("Invalid or expired token") from error
        if claims.get("type") != expected_type:
            raise InvalidTokenError("Token has an invalid type")
        return claims

    @staticmethod
    def _parse_subject(*, claims: dict[str, Any]) -> UserID:
        try:
            return UserID(UUID(str(claims["sub"])))
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidTokenError("Token subject is invalid") from error

    @staticmethod
    def _parse_token_id(*, claims: dict[str, Any]) -> str:
        token_id = claims.get("jti")
        if not isinstance(token_id, str) or not token_id:
            raise InvalidTokenError("Refresh token ID is invalid")
        return token_id

    @staticmethod
    def _remaining_lifetime_seconds(*, claims: dict[str, Any]) -> int:
        try:
            return max(int(claims["exp"]) - int(datetime.now(UTC).timestamp()), 0)
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidTokenError("Refresh token expiry is invalid") from error
