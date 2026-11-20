"""App and client fixtures on SQLite in memory with a few rows per species."""

from collections.abc import Iterator
from decimal import Decimal

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool

from iris_api import create_app
from iris_api.config import Settings
from iris_common.db import make_session_factory
from iris_common.models import Base, Iris, Species

SQLITE_URL = "sqlite+pysqlite:///:memory:"


def _row(id_: int, species: Species, base: str) -> Iris:
    b = Decimal(base)
    return Iris(
        id=id_,
        sepal_length_cm=b,
        sepal_width_cm=b + Decimal("0.1"),
        petal_length_cm=b + Decimal("0.2"),
        petal_width_cm=b + Decimal("0.3"),
        species=species.value,
    )


# ids 1-3 setosa, 4-6 versicolor, 7-9 virginica; every row has distinct values.
SAMPLE_ROWS = [
    _row(i * 3 + n + 1, species, f"{i + 1}.{n}")
    for i, species in enumerate(Species)
    for n in range(3)
]


@pytest.fixture
def engine() -> Iterator[Engine]:
    # StaticPool: every session shares the one in-memory connection, so the tables persist.
    engine = create_engine(
        SQLITE_URL, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        session.add_all(SAMPLE_ROWS)
        session.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def app(engine: Engine) -> Flask:
    return create_app(Settings(database_url=SQLITE_URL), engine=engine)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
