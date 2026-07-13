import asyncio
import csv
from datetime import UTC, datetime
from pathlib import Path

from boutique.application.dataset.ports import DatasetSource
from boutique.domain.dataset.models import OlistDataset

_CUSTOMERS_FILE = "olist_customers_dataset.csv"
_PRODUCTS_FILE = "olist_products_dataset.csv"
_ORDERS_FILE = "olist_orders_dataset.csv"
_ORDER_ITEMS_FILE = "olist_order_items_dataset.csv"


class OlistCsvSource(DatasetSource):
    """CSV source adapter; parsing is separate from database transaction ownership."""

    async def load(self, *, source_dir: Path) -> OlistDataset:
        paths = self._validate_source_dir(source_dir=source_dir)
        customers, products, orders, order_items = await asyncio.to_thread(self._read_rows, paths)
        return OlistDataset(
            customers=customers,
            products=products,
            orders=orders,
            order_items=order_items,
        )

    @staticmethod
    def _validate_source_dir(*, source_dir: Path) -> dict[str, Path]:
        paths = {
            "customers": source_dir / _CUSTOMERS_FILE,
            "products": source_dir / _PRODUCTS_FILE,
            "orders": source_dir / _ORDERS_FILE,
            "order_items": source_dir / _ORDER_ITEMS_FILE,
        }
        missing = [path.name for path in paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing required Olist CSV files: {', '.join(missing)}")
        return paths

    @staticmethod
    def _read_rows(
        paths: dict[str, Path],
    ) -> tuple[
        list[dict[str, str]],
        list[dict[str, str | None]],
        list[dict[str, str | datetime | None]],
        list[dict[str, str | int]],
    ]:
        customers = [
            {"id": row["customer_id"], "state": row["customer_state"]}
            for row in _read_csv(paths["customers"])
        ]
        products = [
            {
                "id": row["product_id"],
                "category": row["product_category_name"] or None,
            }
            for row in _read_csv(paths["products"])
        ]
        orders = [
            {
                "id": row["order_id"],
                "customer_id": row["customer_id"],
                "status": row["order_status"],
                "purchased_at": _parse_timestamp(row["order_purchase_timestamp"]),
                "delivered_at": _parse_timestamp(row["order_delivered_customer_date"]),
            }
            for row in _read_csv(paths["orders"])
        ]
        order_items = [
            {
                "order_id": row["order_id"],
                "line_number": int(row["order_item_id"]),
                "product_id": row["product_id"],
                "quantity": 1,
                "price": row["price"],
                "freight_value": row["freight_value"],
            }
            for row in _read_csv(paths["order_items"])
        ]
        return customers, products, orders, order_items


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
