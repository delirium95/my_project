from pathlib import Path
from zipfile import ZipFile

import pytest

from boutique.domain.dataset.exceptions import KaggleDatasetDownloadError
from boutique.infrastructure.dataset.kaggle_olist_archive import KaggleOlistArchiveDownloaderImpl


def _write_archive(*, archive_path: Path, names: list[str]) -> None:
    with ZipFile(archive_path, "w") as archive:
        for name in names:
            archive.writestr(name, "header\\n")


@pytest.mark.unit
def test_kaggle_archive_extraction_accepts_required_csv_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "olist.zip"
    _write_archive(
        archive_path=archive_path,
        names=[
            "olist_customers_dataset.csv",
            "olist_products_dataset.csv",
            "olist_orders_dataset.csv",
            "olist_order_items_dataset.csv",
        ],
    )
    destination = tmp_path / "extracted"
    destination.mkdir()

    KaggleOlistArchiveDownloaderImpl._extract_archive(
        archive_path=archive_path,
        destination=destination,
    )

    assert KaggleOlistArchiveDownloaderImpl._find_source_dir(destination=destination) == destination


@pytest.mark.unit
def test_kaggle_archive_extraction_rejects_unsafe_paths(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    _write_archive(archive_path=archive_path, names=["../../outside.csv"])
    destination = tmp_path / "extracted"
    destination.mkdir()

    with pytest.raises(KaggleDatasetDownloadError, match="unsafe path"):
        KaggleOlistArchiveDownloaderImpl._extract_archive(
            archive_path=archive_path,
            destination=destination,
        )
