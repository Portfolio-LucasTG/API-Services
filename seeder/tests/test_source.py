from pathlib import Path

import kagglehub
import pytest

from iris_seeder.config import Settings
from iris_seeder.source import VENDORED_CSV, DatasetUnavailableError, resolve_dataset_path


def make_settings(**overrides: object) -> Settings:
    return Settings.model_validate({"database_url": "sqlite://", **overrides})


def fail_download(handle: str) -> str:
    raise ConnectionError(f"no network for {handle}")


def test_dataset_path_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(kagglehub, "dataset_download", fail_download)
    csv = tmp_path / "mine.csv"

    assert resolve_dataset_path(make_settings(dataset_path=csv)) == csv


def test_empty_dataset_path_env_counts_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATASET_PATH", "")

    assert make_settings().dataset_path is None


def test_kaggle_download_used(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "Iris.csv").touch()
    calls: list[str] = []

    def download(handle: str) -> str:
        calls.append(handle)
        return str(tmp_path)

    monkeypatch.setattr(kagglehub, "dataset_download", download)

    assert resolve_dataset_path(make_settings()) == tmp_path / "Iris.csv"
    assert calls == ["uciml/iris"]


def test_download_without_csv_counts_as_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(kagglehub, "dataset_download", lambda _handle: str(tmp_path))

    with pytest.raises(DatasetUnavailableError):
        resolve_dataset_path(make_settings(seed_allow_fallback=False))


def test_download_failure_falls_back_to_vendored(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(kagglehub, "dataset_download", fail_download)

    path = resolve_dataset_path(make_settings(seed_allow_fallback=True))

    assert path == VENDORED_CSV
    assert path.is_file()
    assert [r.levelname for r in caplog.records if "uciml/iris" in r.getMessage()] == ["WARNING"]


def test_download_failure_without_fallback_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(kagglehub, "dataset_download", fail_download)

    with pytest.raises(DatasetUnavailableError, match="uciml/iris"):
        resolve_dataset_path(make_settings(seed_allow_fallback=False))
