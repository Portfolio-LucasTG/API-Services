"""Build SQLAlchemy queries for the API. No Flask imports here."""

import operator

from sqlalchemy import ColumnElement, Select, select

from iris_api.schemas import FILTER_COLUMNS, ListQuery
from iris_common.models import Iris, Species

_OPERATORS = {"": operator.eq, "_min": operator.ge, "_max": operator.le}


def _filter_conditions(query: ListQuery) -> list[ColumnElement[bool]]:
    return [
        op(getattr(Iris, column), value)
        for column in FILTER_COLUMNS
        for suffix, op in _OPERATORS.items()
        if (value := getattr(query, column + suffix)) is not None
    ]


def build_list_query(species: Species, query: ListQuery) -> Select[Iris]:
    """Select the rows of ``species`` matching every filter in ``query``, ordered by id."""
    return (
        select(Iris)
        .where(Iris.species == species.value, *_filter_conditions(query))
        .order_by(Iris.id)
    )


def build_retrieve_query(species: Species, id_: int) -> Select[Iris]:
    """Select the row ``id_`` only if it belongs to ``species``."""
    return select(Iris).where(Iris.id == id_, Iris.species == species.value)
