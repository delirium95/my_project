from pathlib import Path
from tempfile import TemporaryDirectory

from boutique.application.dashboard.cache_keys import dashboard_cache_prefix
from boutique.application.dataset.interfaces import (
    ImportKaggleOlistDatasetUseCase,
    SeedOlistDatasetUseCase,
)
from boutique.application.dataset.ports import DatasetSource, KaggleOlistArchiveDownloader
from boutique.domain.common.cache import BaseCacheService
from boutique.domain.dataset.models import SeedResult
from boutique.domain.shared.unit_of_work import UnitOfWork


class SeedOlistDatasetUseCaseImpl(SeedOlistDatasetUseCase):
    """Import source data, then invalidate only dashboard read models."""

    def __init__(
        self,
        *,
        source: DatasetSource,
        unit_of_work: UnitOfWork,
        cache: BaseCacheService,
    ) -> None:
        self._source = source
        self._unit_of_work = unit_of_work
        self._cache = cache

    async def __call__(self, *, source_dir: Path, replace_existing: bool = False) -> SeedResult:
        dataset = await self._source.load(source_dir=source_dir)
        async with self._unit_of_work as unit_of_work:
            result = await unit_of_work.dataset.replace_olist(
                dataset=dataset,
                replace_existing=replace_existing,
            )
            await unit_of_work.commit()
        await self._cache.invalidate_prefix(prefix=dashboard_cache_prefix())
        return result


class ImportKaggleOlistDatasetUseCaseImpl(ImportKaggleOlistDatasetUseCase):
    """Keep remote download details outside the HTTP layer and reuse the seed workflow."""

    def __init__(
        self,
        *,
        archive_downloader: KaggleOlistArchiveDownloader,
        seed_olist_dataset: SeedOlistDatasetUseCase,
    ) -> None:
        self._archive_downloader = archive_downloader
        self._seed_olist_dataset = seed_olist_dataset

    async def __call__(self, *, replace_existing: bool = False) -> SeedResult:
        with TemporaryDirectory(prefix="boutique-olist-") as temporary_directory:
            source_dir = await self._archive_downloader.download(
                destination=Path(temporary_directory)
            )
            return await self._seed_olist_dataset(
                source_dir=source_dir,
                replace_existing=replace_existing,
            )
