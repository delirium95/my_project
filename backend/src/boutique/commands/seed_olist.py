import argparse
import asyncio
from pathlib import Path

from boutique.bootstrap.container import build_container, shutdown_container
from boutique.config import get_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import the Olist CSV dataset into PostgreSQL.")
    parser.add_argument(
        "source_dir", type=Path, help="Directory containing the extracted Olist CSV files"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing Olist data before importing; required for re-seeding",
    )
    return parser.parse_args()


async def run(*, source_dir: Path, replace_existing: bool) -> None:
    settings = get_settings()
    container = build_container(settings=settings)
    try:
        result = await container.seed_olist_dataset()(
            source_dir=source_dir,
            replace_existing=replace_existing,
        )
    finally:
        await shutdown_container(container=container)
    print(
        "Seeded "
        f"{result.customers} customers, {result.products} products, "
        f"{result.orders} orders, and {result.order_items} order items."
    )


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(source_dir=args.source_dir, replace_existing=args.replace))
