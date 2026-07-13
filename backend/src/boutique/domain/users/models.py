from pydantic import field_validator

from boutique.domain.common.models import DomainModel
from boutique.domain.ids import AuthSubject, UserID


class User(DomainModel):
    id: UserID
    auth_subject: AuthSubject
    email: str
    display_name: str | None = None
    password_hash: str
    is_active: bool = True

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, email: str) -> str:
        normalized = email.strip().lower()
        if "@" not in normalized or len(normalized) > 320:
            raise ValueError("Email must be a valid address up to 320 characters")
        return normalized

    @field_validator("display_name", mode="after")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized or len(normalized) > 100:
            raise ValueError("Display name must contain 1 to 100 characters")
        return normalized
