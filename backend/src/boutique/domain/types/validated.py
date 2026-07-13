from typing import Annotated

from pydantic import AfterValidator


def validate_identifier(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 255:
        raise ValueError("Identifier must be a non-empty string up to 255 characters")
    return normalized


Identifier = Annotated[str, AfterValidator(validate_identifier)]
