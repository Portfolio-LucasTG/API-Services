"""Each request reads one consistent snapshot (REPEATABLE READ on PostgreSQL)."""

import os

import pytest
from sqlalchemy import text

from iris_api import create_app
from iris_api.config import Settings
from iris_api.db import get_session


def test_engine_from_database_url_uses_repeatable_read() -> None:
    # Building the engine doesn't connect, so no database is needed.
    app = create_app(Settings(database_url="postgresql+psycopg://u:p@localhost:1/x"))

    with app.app_context():
        bind = get_session().get_bind()

    assert bind.get_execution_options()["isolation_level"] == "REPEATABLE READ"


@pytest.mark.integration
def test_request_transaction_is_repeatable_read_on_postgres() -> None:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    app = create_app(Settings(database_url=url))

    with app.app_context():
        level = get_session().execute(text("SHOW transaction_isolation")).scalar()

    assert level == "repeatable read"
