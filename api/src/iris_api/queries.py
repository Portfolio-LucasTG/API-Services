"""Build SQLAlchemy queries for the API. No Flask imports here."""

from collections.abc import Iterable

from sqlalchemy import ColumnElement, Select, select

from iris_common.models import Iris, Species


def build_list_query(species: Species, filters: Iterable[ColumnElement[bool]] = ()) -> Select[Iris]:
    """Select the rows of ``species`` matching every condition in ``filters``, ordered by id."""
    return select(Iris).where(Iris.species == species.value, *filters).order_by(Iris.id)


def build_retrieve_query(species: Species, id_: int) -> Select[Iris]:
    """Select the row ``id_`` only if it belongs to ``species``."""
    return select(Iris).where(Iris.id == id_, Iris.species == species.value)
