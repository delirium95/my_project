from abc import ABC, abstractmethod

from boutique.domain.dataset.models import OlistDataset, SeedResult


class DatasetRepository(ABC):
    """Write contract for replacing the immutable Olist dataset."""

    @abstractmethod
    async def replace_olist(
        self,
        *,
        dataset: OlistDataset,
        replace_existing: bool,
    ) -> SeedResult:
        """Stage one complete Olist import in the current unit of work."""
