import logging
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError

from iris_seeder import __main__ as entry
from iris_seeder.parsing import IrisRow

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pw@localhost:1/none")
    monkeypatch.setenv("DATASET_PATH", str(FIXTURES / "small.csv"))
    monkeypatch.setenv("LOG_LEVEL", "INFO")


@pytest.fixture(autouse=True)
def restore_root_log_level() -> Iterator[None]:
    """main() sets the root logger level; undo it so later tests are unaffected."""
    root = logging.getLogger()
    level = root.level
    yield
    root.setLevel(level)


def fake_upsert(_engine: Engine, rows: Sequence[IrisRow]) -> int:
    return len(rows)


def test_success_returns_0(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(entry, "upsert_rows", fake_upsert)

    assert entry.main() == 0
    assert "Upserted 6 rows" in caplog.text
    assert "'setosa': 2" in caplog.text


def test_parse_error_returns_1(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(entry, "upsert_rows", fake_upsert)
    monkeypatch.setenv("DATASET_PATH", str(FIXTURES / "bad_number.csv"))

    assert entry.main() == 1
    assert "bad_number.csv:" in caplog.text


def test_db_error_returns_1(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_upsert(_engine: Engine, _rows: Sequence[IrisRow]) -> int:
        raise OperationalError("INSERT", {}, ConnectionRefusedError("db down"))

    monkeypatch.setattr(entry, "upsert_rows", broken_upsert)

    assert entry.main() == 1


def test_missing_database_url_returns_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL")

    assert entry.main() == 1


def test_log_level_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entry, "upsert_rows", fake_upsert)
    monkeypatch.setenv("LOG_LEVEL", "warning")

    assert entry.main() == 0
    assert logging.getLogger().level == logging.WARNING


def test_invalid_log_level_returns_1(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "verbose")

    assert entry.main() == 1
    assert "log_level" in caplog.text
