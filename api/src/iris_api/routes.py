"""HTTP routes of the read-only API."""

import logging

from flask import Blueprint
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from iris_api.db import get_session

logger = logging.getLogger("iris_api")

bp = Blueprint("iris", __name__)


@bp.get("/health")
def health() -> tuple[dict[str, str], int]:
    """Report whether the database answers ``SELECT 1``."""
    try:
        get_session().execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Health check failed")
        return {"status": "unavailable"}, 503
    return {"status": "ok"}, 200
