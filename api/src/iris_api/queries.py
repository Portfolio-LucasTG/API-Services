"""Build SQLAlchemy queries for the API. No Flask imports here."""

import operator

from sqlalchemy import ColumnElement, Select, UnaryExpression, func, select
from sqlalchemy.orm import InstrumentedAttribute

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


def _order(order_by: str) -> UnaryExpression[object]:
    """``"<column>+"`` -> ascending, ``"<column>-"`` -> descending; column from FILTER_COLUMNS."""
    column, direction = order_by[:-1], order_by[-1:]
    if column not in FILTER_COLUMNS or direction not in ("+", "-"):
        raise ValueError(f"Invalid order rule: {order_by!r}")
    attr: InstrumentedAttribute[object] = getattr(Iris, column)
    return attr.asc() if direction == "+" else attr.desc()


def build_list_query(
    species: Species, query: ListQuery, order_by: str | None = None
) -> Select[Iris]:
    """Select the rows of ``species`` matching every filter in ``query``.

    Unordered unless ``order_by`` is given (e.g. ``"id+"``), so the count query skips sorting.
    """
    stmt = select(Iris).where(Iris.species == species.value, *_filter_conditions(query))
    return stmt if order_by is None else stmt.order_by(_order(order_by))


def build_page_query(
    species: Species, query: ListQuery, order_by: str | None = None
) -> Select[Iris]:
    """``build_list_query`` limited to page ``query.page`` of ``query.per_page`` rows."""
    return (
        build_list_query(species, query, order_by)
        .limit(query.per_page)
        .offset((query.page - 1) * query.per_page)
    )


def build_count_query(species: Species, query: ListQuery) -> Select[int]:
    """Count the rows ``build_list_query`` would return (same filters, no ordering)."""
    return select(func.count()).select_from(build_list_query(species, query).subquery())


def build_retrieve_query(species: Species, id_: int) -> Select[Iris]:
    """Select the row ``id_`` only if it belongs to ``species``."""
    return select(Iris).where(Iris.id == id_, Iris.species == species.value)
