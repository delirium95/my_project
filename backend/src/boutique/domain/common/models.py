from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Validated domain state with no undeclared fields."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ValueObject(DomainModel):
    """Immutable, validated value with structural equality."""

    model_config = ConfigDict(extra="forbid", frozen=True)
