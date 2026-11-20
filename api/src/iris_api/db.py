"""One SQLAlchemy session per request, closed when the app context ends."""

from flask import Flask, current_app, g
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from iris_common.db import make_session_factory

_FACTORY_KEY = "iris_session_factory"


def init_db(app: Flask, engine: Engine) -> None:
    """Attach a session factory for ``engine`` to ``app`` and close sessions on teardown."""
    app.extensions[_FACTORY_KEY] = make_session_factory(engine)
    app.teardown_appcontext(_close_session)


def get_session() -> Session:
    """Return the session of the current request, creating it on first use."""
    if "db_session" not in g:
        g.db_session = current_app.extensions[_FACTORY_KEY]()
    session: Session = g.db_session
    return session


def _close_session(_exc: BaseException | None) -> None:
    session: Session | None = g.pop("db_session", None)
    if session is not None:
        session.close()
