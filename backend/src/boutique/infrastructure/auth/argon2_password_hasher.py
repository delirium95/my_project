from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from boutique.domain.auth.exceptions import InvalidCredentialsError
from boutique.domain.auth.interfaces import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Argon2id password adapter based on the Stock Picker implementation."""

    def __init__(self) -> None:
        self._hasher = Argon2Hasher()

    def hash(self, *, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, *, password: str, password_hash: str) -> None:
        try:
            self._hasher.verify(hash=password_hash, password=password)
        except (InvalidHashError, VerifyMismatchError) as error:
            raise InvalidCredentialsError("Invalid email or password") from error
