"""Read-only Flask REST API for the Iris dataset."""

import logging

from flask import Flask
from sqlalchemy import Engine

from iris_api.config import Settings
from iris_api.db import init_db
from iris_api.errors import register_error_handlers
from iris_api.routes import bp
from iris_common.db import make_engine


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> Flask:
    """Build the Flask app; ``engine`` overrides the one built from ``DATABASE_URL`` (tests)."""
    settings = settings or Settings()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    app = Flask(__name__)
    init_db(app, engine or make_engine(settings.database_url))
    register_error_handlers(app)
    app.register_blueprint(bp)
    return app
