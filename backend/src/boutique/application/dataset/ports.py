from abc import ABC, abstractmethod
from pathlib import Path

from boutique.domain.dataset.models import OlistDataset


class DatasetSource(ABC):
    @abstractmethod
    async def load(self, *, source_dir: Path) -> OlistDataset:
        """Read and normalize a dataset from the supplied source directory."""


class KaggleOlistArchiveDownloader(ABC):
    @abstractmethod
    async def download(self, *, destination: Path) -> Path:
        """Download and extract the configured Olist archive into ``destination``."""
