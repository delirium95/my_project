import asyncio
import base64
import stat
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

from boutique.application.dataset.ports import KaggleOlistArchiveDownloader
from boutique.domain.dataset.exceptions import (
    KaggleCredentialsMissingError,
    KaggleDatasetDownloadError,
)

_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
_MAX_EXTRACTED_BYTES = 512 * 1024 * 1024
_REQUIRED_FILES = (
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
)


class KaggleOlistArchiveDownloaderImpl(KaggleOlistArchiveDownloader):
    """Download the fixed Olist Kaggle archive using credentials held only by the server."""

    def __init__(self, *, dataset: str, username: str | None, key: str | None) -> None:
        self._dataset = dataset
        self._username = username
        self._key = key

    async def download(self, *, destination: Path) -> Path:
        if not self._username or not self._key:
            raise KaggleCredentialsMissingError(
                "Set KAGGLE_USERNAME and KAGGLE_KEY on the API server before importing."
            )
        return await asyncio.to_thread(self._download_and_extract, destination)

    def _download_and_extract(self, destination: Path) -> Path:
        archive_path = destination / "olist-kaggle.zip"
        destination.mkdir(parents=True, exist_ok=True)
        try:
            self._download_archive(archive_path=archive_path)
            self._extract_archive(archive_path=archive_path, destination=destination)
            return self._find_source_dir(destination=destination)
        except (HTTPError, URLError, OSError, BadZipFile) as error:
            raise KaggleDatasetDownloadError(
                "Could not download or extract the Olist dataset from Kaggle."
            ) from error
        finally:
            archive_path.unlink(missing_ok=True)

    def _download_archive(self, *, archive_path: Path) -> None:
        encoded_credentials = base64.b64encode(f"{self._username}:{self._key}".encode()).decode(
            "ascii"
        )
        request = Request(
            url=(
                f"https://www.kaggle.com/api/v1/datasets/download/{quote(self._dataset, safe='/')}"
            ),
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "User-Agent": "boutique-analytics/0.1",
            },
        )
        with urlopen(request, timeout=180) as response, archive_path.open("wb") as archive_file:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > _MAX_ARCHIVE_BYTES:
                raise KaggleDatasetDownloadError("The Kaggle archive exceeds the allowed size.")
            downloaded_bytes = 0
            while chunk := response.read(1024 * 1024):
                downloaded_bytes += len(chunk)
                if downloaded_bytes > _MAX_ARCHIVE_BYTES:
                    raise KaggleDatasetDownloadError("The Kaggle archive exceeds the allowed size.")
                archive_file.write(chunk)

    @staticmethod
    def _extract_archive(*, archive_path: Path, destination: Path) -> None:
        destination_root = destination.resolve()
        with ZipFile(archive_path) as archive:
            extracted_size = 0
            for member in archive.infolist():
                target = (destination / member.filename).resolve()
                is_symlink = stat.S_ISLNK(member.external_attr >> 16)
                if not target.is_relative_to(destination_root) or is_symlink:
                    raise KaggleDatasetDownloadError("The Kaggle archive contains an unsafe path.")
                extracted_size += member.file_size
                if extracted_size > _MAX_EXTRACTED_BYTES:
                    raise KaggleDatasetDownloadError(
                        "The extracted Kaggle data exceeds the allowed size."
                    )
                archive.extract(member, path=destination)

    @staticmethod
    def _find_source_dir(*, destination: Path) -> Path:
        for customers_file in destination.rglob(_REQUIRED_FILES[0]):
            candidate = customers_file.parent
            if all((candidate / filename).is_file() for filename in _REQUIRED_FILES):
                return candidate
        raise KaggleDatasetDownloadError(
            "The Kaggle archive does not contain the required Olist CSV files."
        )
