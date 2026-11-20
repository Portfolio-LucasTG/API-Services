from pathlib import Path

import pytest
from flask.testing import FlaskClient
from sqlalchemy import create_engine

from iris_api import create_app
from iris_api.config import Settings


def test_health_ok(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_unavailable_when_db_is_down(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # A database file in a directory that doesn't exist: connecting raises OperationalError.
    url = f"sqlite+pysqlite:///{tmp_path / 'missing' / 'iris.db'}"
    app = create_app(Settings(database_url=url), engine=create_engine(url))

    response = app.test_client().get("/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
    assert "Health check failed" in caplog.text


def test_create_app_reads_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    assert create_app().test_client().get("/health").status_code == 200
