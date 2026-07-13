from uuid import UUID

import pytest

from boutique.application.auth.use_cases import LoginUseCaseImpl, RegisterUserUseCaseImpl
from boutique.domain.auth.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from boutique.domain.auth.interfaces import PasswordHasher, TokenService
from boutique.domain.auth.models import LoginInput, RegisterUserInput, TokenPair
from boutique.domain.ids import UserID
from tests.fakes.unit_of_work import FakeUnitOfWork


class FakePasswordHasher(PasswordHasher):
    def hash(self, *, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, *, password: str, password_hash: str) -> None:
        if password_hash != f"hashed:{password}":
            raise InvalidCredentialsError("Invalid email or password")


class FakeTokenService(TokenService):
    def issue(self, *, user_id: UserID) -> TokenPair:
        return TokenPair(
            access_token=f"access:{user_id}",
            refresh_token=f"refresh:{user_id}",
            expires_in_seconds=3_600,
        )

    def decode_access(self, *, token: str) -> UserID:
        return UserID(UUID(token.removeprefix("access:")))

    async def rotate_refresh(self, *, refresh_token: str) -> TokenPair:
        user_id = UserID(UUID(refresh_token.removeprefix("refresh:")))
        return self.issue(user_id=user_id)

    async def revoke_refresh(self, *, refresh_token: str) -> None:
        return None


@pytest.mark.unit
async def test_register_user_hashes_password_and_commits_via_shared_uow() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = RegisterUserUseCaseImpl(
        password_hasher=FakePasswordHasher(),
        unit_of_work=unit_of_work,
    )

    user = await use_case(
        input_data=RegisterUserInput(
            email="  PERSON@example.com ",
            password="safe-password",
            display_name="Person",
        )
    )

    assert user.email == "person@example.com"
    assert user.password_hash == "hashed:safe-password"
    assert unit_of_work.users.users[user.id] == user
    assert unit_of_work.commit_count == 1


@pytest.mark.unit
async def test_register_user_rejects_duplicate_email() -> None:
    unit_of_work = FakeUnitOfWork()
    use_case = RegisterUserUseCaseImpl(
        password_hasher=FakePasswordHasher(),
        unit_of_work=unit_of_work,
    )
    input_data = RegisterUserInput(email="person@example.com", password="safe-password")
    await use_case(input_data=input_data)

    with pytest.raises(EmailAlreadyRegisteredError):
        await use_case(input_data=input_data)


@pytest.mark.unit
async def test_login_returns_access_token_only_for_valid_credentials() -> None:
    unit_of_work = FakeUnitOfWork()
    register_user = RegisterUserUseCaseImpl(
        password_hasher=FakePasswordHasher(),
        unit_of_work=unit_of_work,
    )
    user = await register_user(
        input_data=RegisterUserInput(email="person@example.com", password="safe-password")
    )
    login = LoginUseCaseImpl(
        password_hasher=FakePasswordHasher(),
        token_service=FakeTokenService(),
        unit_of_work=unit_of_work,
    )

    token = await login(input_data=LoginInput(email=user.email, password="safe-password"))

    assert token.access_token == f"access:{user.id}"
    with pytest.raises(InvalidCredentialsError):
        await login(input_data=LoginInput(email=user.email, password="wrong-password"))
