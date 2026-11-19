from sqlalchemy import text

from iris_common.db import make_engine, make_session_factory


def test_make_engine_connects() -> None:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT 1")) == 1
    engine.dispose()


def test_session_factory_is_bound_to_engine() -> None:
    engine = make_engine("sqlite+pysqlite:///:memory:")
    factory = make_session_factory(engine)
    with factory() as session:
        assert session.get_bind() is engine
        assert session.scalar(text("SELECT 1")) == 1
    engine.dispose()
