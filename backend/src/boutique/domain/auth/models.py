from pydantic import Field, field_validator

from boutique.domain.common.models import ValueObject


class RegisterUserInput(ValueObject):
    email: str
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        normalized = email.strip().lower()
        if "@" not in normalized or len(normalized) > 320:
            raise ValueError("Email must be a valid address up to 320 characters")
        return normalized


class LoginInput(ValueObject):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        return email.strip().lower()


class TokenPair(ValueObject):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
