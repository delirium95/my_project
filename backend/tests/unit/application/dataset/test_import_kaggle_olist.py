from pathlib import Path

import pytest

from boutique.application.dataset.interfaces import SeedOlistDatasetUseCase
from boutique.application.dataset.ports import KaggleOlistArchiveDownloader
from boutique.application.dataset.use_cases import ImportKaggleOlistDatasetUseCaseImpl
from boutique.domain.dataset.models import SeedResult


class FakeKaggleArchiveDownloader(KaggleOlistArchiveDownloader):
    def __init__(self) -> None:
        self.destination: Path | None = None

    async def download(self, *, destination: Path) -> Path:
        self.destination = destination
        return destination


class FakeSeedOlistDatasetUseCase(SeedOlistDatasetUseCase):
    def __init__(self) -> None:
        self.request: tuple[Path, bool] | None = None

    async def __call__(self, *, source_dir: Path, replace_existing: bool = False) -> SeedResult:
        self.request = (source_dir, replace_existing)
        return SeedResult(customers=1, products=2, orders=3, order_items=4)


@pytest.mark.unit
async def test_kaggle_import_downloads_to_a_temporary_directory_then_reuses_seed_flow() -> None:
    downloader = FakeKaggleArchiveDownloader()
    seed_olist_dataset = FakeSeedOlistDatasetUseCase()

    result = await ImportKaggleOlistDatasetUseCaseImpl(
        archive_downloader=downloader,
        seed_olist_dataset=seed_olist_dataset,
    )(replace_existing=True)

    assert result.orders == 3
    assert downloader.destination is not None
    assert seed_olist_dataset.request == (downloader.destination, True)
    assert not downloader.destination.exists()
