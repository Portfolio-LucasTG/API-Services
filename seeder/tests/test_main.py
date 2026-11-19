from collections.abc import Sequence
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
