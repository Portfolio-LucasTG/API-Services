"""``queries.py`` on its own, without Flask."""

from sqlalchemy import Engine

from iris_api.queries import build_list_query, build_retrieve_query
from iris_api.schemas import ListQuery
from iris_common.db import make_session_factory
from iris_common.models import Species


def test_build_list_query_applies_filters(engine: Engine) -> None:
    query = build_list_query(Species.VERSICOLOR, ListQuery(id_min=5))

    with make_session_factory(engine)() as session:
        assert [row.id for row in session.scalars(query)] == [5, 6]


def test_build_retrieve_query_matches_own_species(engine: Engine) -> None:
    with make_session_factory(engine)() as session:
        row = session.scalars(build_retrieve_query(Species.VIRGINICA, 8)).one()

    assert row.id == 8


def test_build_retrieve_query_ignores_other_species(engine: Engine) -> None:
    with make_session_factory(engine)() as session:
        assert session.scalars(build_retrieve_query(Species.SETOSA, 8)).one_or_none() is None
