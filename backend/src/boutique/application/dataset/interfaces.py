from abc import ABC, abstractmethod
from pathlib import Path

from boutique.domain.dataset.models import SeedResult


class SeedOlistDatasetUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, source_dir: Path, replace_existing: bool = False) -> SeedResult:
        """Load the Olist CSV dataset and invalidate affected read caches."""


class ImportKaggleOlistDatasetUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, replace_existing: bool = False) -> SeedResult:
        """Download the configured Kaggle Olist archive and import its CSV files."""
