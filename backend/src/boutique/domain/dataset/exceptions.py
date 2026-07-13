class DatasetAlreadySeededError(RuntimeError):
    """Raised when a non-empty dataset would be overwritten without approval."""


class KaggleCredentialsMissingError(RuntimeError):
    """Raised when an import is requested without server-side Kaggle credentials."""


class KaggleDatasetDownloadError(RuntimeError):
    """Raised when the configured Kaggle dataset cannot be downloaded or extracted."""
