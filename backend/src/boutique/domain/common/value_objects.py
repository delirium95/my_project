from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from pydantic import field_validator

from boutique.domain.common.exceptions import DomainValidationError
from boutique.domain.common.models import ValueObject


class Money(ValueObject):
    amount: Decimal
    currency: str = "BRL"

    @field_validator("amount", mode="after")
    @classmethod
    def validate_amount(cls, amount: Decimal) -> Decimal:
        try:
            amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError) as error:
            raise ValueError("Money amount must be a finite decimal") from error
        if not amount.is_finite():
            raise ValueError("Money amount must be finite")
        return amount

    @field_validator("currency", mode="after")
    @classmethod
    def validate_currency(cls, currency: str) -> str:
        currency = currency.upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return currency

    @classmethod
    def zero(cls, *, currency: str = "BRL") -> "Money":
        return cls(amount=Decimal("0"), currency=currency)

    def add(self, *, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise DomainValidationError("Cannot add money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def divide(self, *, divisor: int) -> "Money":
        if divisor <= 0:
            raise DomainValidationError("Money can only be divided by a positive number")
        return Money(amount=self.amount / divisor, currency=self.currency)
