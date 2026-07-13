from pathlib import Path
from typing import Any

import pytest

from boutique.application.dataset.ports import DatasetSource
from boutique.application.dataset.use_cases import SeedOlistDatasetUseCaseImpl
from boutique.domain.common.cache import BaseCacheService
from boutique.domain.dataset.models import OlistDataset
from tests.fakes.unit_of_work import FakeUnitOfWork


class FakeDatasetSource(DatasetSource):
    def __init__(self, dataset: OlistDataset) -> None:
        self.dataset = dataset
        self.request: Path | None = None

    async def load(self, *, source_dir: Path) -> OlistDataset:
        self.request = source_dir
        return self.dataset


class FakeCacheService(BaseCacheService):
    def __init__(self) -> None:
        self.invalidated_prefix: str | None = None

    async def get(self, *, key: str) -> dict[str, Any] | None:
        return None

    async def set(self, *, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        return None

    async def invalidate_prefix(self, *, prefix: str) -> None:
        self.invalidated_prefix = prefix


@pytest.mark.unit
async def test_seed_olist_commits_via_shared_uow_and_invalidates_cache_after_success() -> None:
    dataset = OlistDataset(
        customers=[{"id": "customer-1", "state": "SP"}],
        products=[{"id": "product-1", "category": "books"}],
        orders=[{"id": "order-1", "customer_id": "customer-1"}],
        order_items=[{"order_id": "order-1", "line_number": 1, "product_id": "product-1"}],
    )
    source = FakeDatasetSource(dataset)
    unit_of_work = FakeUnitOfWork()
    cache = FakeCacheService()
    source_dir = Path("/tmp/olist")

    result = await SeedOlistDatasetUseCaseImpl(
        source=source,
        unit_of_work=unit_of_work,
        cache=cache,
    )(
        source_dir=source_dir,
        replace_existing=True,
    )

    assert result.orders == 1
    assert source.request == source_dir
    assert unit_of_work.dataset.request == (dataset, True)
    assert unit_of_work.commit_count == 1
    assert cache.invalidated_prefix == "dashboard:v1:"
