"""Shared fixtures for iris_common tests.

``pg_engine`` is the reusable pattern for integration tests: it skips when
``TEST_DATABASE_URL`` is unset, creates the tables and drops them afterwards.
"""

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from iris_common.db import make_engine, make_session_factory
from iris_common.models import Base


@pytest.fixture
def sqlite_engine() -> Iterator[Engine]:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(sqlite_engine: Engine) -> Iterator[Session]:
    with make_session_factory(sqlite_engine)() as session:
        yield session


@pytest.fixture(scope="session")
def pg_engine() -> Iterator[Engine]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()
