"""``queries.py`` on its own, without Flask."""

import pytest
from sqlalchemy import Engine

from iris_api.queries import (
    build_count_query,
    build_list_query,
    build_page_query,
    build_retrieve_query,
)
from iris_api.schemas import ListQuery
from iris_common.db import make_session_factory
from iris_common.models import Species


def test_build_list_query_applies_filters(engine: Engine) -> None:
    query = build_list_query(Species.VERSICOLOR, ListQuery(id_min=5), order_by="id+")

    with make_session_factory(engine)() as session:
        assert [row.id for row in session.scalars(query)] == [5, 6]


def test_build_retrieve_query_matches_own_species(engine: Engine) -> None:
    with make_session_factory(engine)() as session:
        row = session.scalars(build_retrieve_query(Species.VIRGINICA, 8)).one()

    assert row.id == 8


def test_build_retrieve_query_ignores_other_species(engine: Engine) -> None:
    with make_session_factory(engine)() as session:
        assert session.scalars(build_retrieve_query(Species.SETOSA, 8)).one_or_none() is None


def test_build_page_query_limits_and_offsets(engine: Engine) -> None:
    query = build_page_query(Species.VIRGINICA, ListQuery(page=2, per_page=2), order_by="id+")

    with make_session_factory(engine)() as session:
        assert [row.id for row in session.scalars(query)] == [9]


def test_build_count_query_uses_filters(engine: Engine) -> None:
    query = build_count_query(Species.VIRGINICA, ListQuery(id_min=8, page=5))

    with make_session_factory(engine)() as session:
        assert session.scalar(query) == 2


def test_build_list_query_is_unordered_by_default() -> None:
    assert "ORDER BY" not in str(build_list_query(Species.SETOSA, ListQuery()))


@pytest.mark.parametrize(
    ("order_by", "ids"), [("id+", [1, 2, 3]), ("id-", [3, 2, 1]), ("sepal_length_cm-", [3, 2, 1])]
)
def test_build_list_query_orders_by_rule(engine: Engine, order_by: str, ids: list[int]) -> None:
    query = build_list_query(Species.SETOSA, ListQuery(), order_by=order_by)

    with make_session_factory(engine)() as session:
        assert [row.id for row in session.scalars(query)] == ids


@pytest.mark.parametrize("order_by", ["id", "species+", "id*", ""])
def test_build_list_query_rejects_bad_order_rule(order_by: str) -> None:
    with pytest.raises(ValueError, match="Invalid order rule"):
        build_list_query(Species.SETOSA, ListQuery(), order_by=order_by)
