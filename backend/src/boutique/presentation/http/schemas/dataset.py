from boutique.domain.dataset.models import SeedResult
from boutique.presentation.http.schemas.base import Schema


class KaggleOlistImportRequestSchema(Schema):
    replace_existing: bool = False


class DatasetImportResponseSchema(Schema):
    source: str
    customers: int
    products: int
    orders: int
    order_items: int

    @classmethod
    def from_seed_result(cls, *, result: SeedResult) -> "DatasetImportResponseSchema":
        return cls(
            source="Kaggle Olist dataset",
            customers=result.customers,
            products=result.products,
            orders=result.orders,
            order_items=result.order_items,
        )
