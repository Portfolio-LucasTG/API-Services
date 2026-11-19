"""Decide which CSV file the seeder loads."""

import logging
from pathlib import Path

import kagglehub

from iris_seeder.config import Settings

logger = logging.getLogger(__name__)

VENDORED_CSV = Path(__file__).resolve().parents[2] / "data" / "Iris.csv"


class DatasetUnavailableError(RuntimeError):
    """No dataset could be obtained."""


def resolve_dataset_path(settings: Settings) -> Path:
    """Return ``DATASET_PATH``, else the Kaggle download, else (if allowed) the vendored copy."""
    if settings.dataset_path is not None:
        logger.info("Using DATASET_PATH %s", settings.dataset_path)
        return settings.dataset_path
    try:
        folder = kagglehub.dataset_download(settings.kaggle_dataset)
    except Exception as exc:  # noqa: BLE001 - kagglehub raises network, HTTP and OS errors alike
        return _fallback(settings, f"download failed ({exc})", exc)
    path = Path(folder) / "Iris.csv"
    if not path.is_file():
        return _fallback(settings, f"{path} not found in download", None)
    logger.info("Using downloaded dataset %s", path)
    return path


def _fallback(settings: Settings, reason: str, cause: Exception | None) -> Path:
    """Return the vendored CSV if allowed, else raise ``DatasetUnavailableError``."""
    if not settings.seed_allow_fallback:
        raise DatasetUnavailableError(f"{settings.kaggle_dataset}: {reason}") from cause
    logger.warning("%s: %s; using %s", settings.kaggle_dataset, reason, VENDORED_CSV)
    return VENDORED_CSV
