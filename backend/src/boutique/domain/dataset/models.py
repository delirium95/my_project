from typing import Any

from boutique.domain.common.models import DomainModel, ValueObject


class OlistDataset(DomainModel):
    """Validated, normalized rows ready for the Olist persistence adapter."""

    customers: list[dict[str, Any]]
    products: list[dict[str, Any]]
    orders: list[dict[str, Any]]
    order_items: list[dict[str, Any]]


class SeedResult(ValueObject):
    customers: int
    products: int
    orders: int
    order_items: int
