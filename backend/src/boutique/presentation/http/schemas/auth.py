from pydantic import EmailStr, Field

from boutique.presentation.http.schemas.base import Schema


class RegisterUserRequestSchema(Schema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=100)


class LoginRequestSchema(Schema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponseSchema(Schema):
    id: str
    email: str
    display_name: str | None


class AccessTokenResponseSchema(Schema):
    access_token: str
    token_type: str
    expires_in_seconds: int
