import os
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from iris_common.db import make_engine
from iris_common.models import Base, Iris
from iris_seeder.loader import upsert_rows
from iris_seeder.parsing import read_rows

FIXTURES = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.integration


@pytest.fixture
def pg_engine() -> Iterator[Engine]:
    """Empty PostgreSQL database per test (same pattern as ``common/tests/conftest.py``)."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    engine = make_engine(url)
    Base.metadata.drop_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def count_rows(engine: Engine) -> int:
    with Session(engine) as session:
        return session.scalar(select(func.count()).select_from(Iris)) or 0


def test_upsert_inserts_rows(pg_engine: Engine) -> None:
    rows = read_rows(FIXTURES / "small.csv")

    assert upsert_rows(pg_engine, rows) == 6
    assert count_rows(pg_engine) == 6
    with Session(pg_engine) as session:
        first = session.get_one(Iris, 1)
    assert (first.sepal_length_cm, first.species) == (Decimal("5.1"), "setosa")


def test_upsert_twice_keeps_rows(pg_engine: Engine) -> None:
    rows = read_rows(FIXTURES / "small.csv")

    upsert_rows(pg_engine, rows)
    upsert_rows(pg_engine, rows)

    assert count_rows(pg_engine) == 6


def test_upsert_updates_changed_value(pg_engine: Engine) -> None:
    rows = read_rows(FIXTURES / "small.csv")
    upsert_rows(pg_engine, rows)
    changed = [rows[0].model_copy(update={"petal_width_cm": Decimal("9.9")}), *rows[1:]]

    upsert_rows(pg_engine, changed)

    with Session(pg_engine) as session:
        assert session.get_one(Iris, 1).petal_width_cm == Decimal("9.9")
    assert count_rows(pg_engine) == 6


def test_upsert_nothing_creates_table(pg_engine: Engine) -> None:
    assert upsert_rows(pg_engine, []) == 0
    assert count_rows(pg_engine) == 0
