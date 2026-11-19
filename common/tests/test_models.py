from decimal import Decimal

import pytest
from sqlalchemy import Engine, delete, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from iris_common.db import make_session_factory
from iris_common.models import Iris, Species


def _iris(id_: int = 1, species: str = Species.SETOSA) -> Iris:
    return Iris(
        id=id_,
        sepal_length_cm=Decimal("5.1"),
        sepal_width_cm=Decimal("3.5"),
        petal_length_cm=Decimal("1.4"),
        petal_width_cm=Decimal("0.2"),
        species=species,
    )


def test_species_values() -> None:
    assert [s.value for s in Species] == ["setosa", "versicolor", "virginica"]


def test_table_is_created(sqlite_engine: Engine) -> None:
    inspector = inspect(sqlite_engine)
    assert "iris" in inspector.get_table_names()
    columns = {c["name"]: c for c in inspector.get_columns("iris")}
    assert set(columns) == {
        "id",
        "sepal_length_cm",
        "sepal_width_cm",
        "petal_length_cm",
        "petal_width_cm",
        "species",
    }
    assert not any(c["nullable"] for c in columns.values())
    assert any(ix["column_names"] == ["species"] for ix in inspector.get_indexes("iris"))


def test_round_trip_keeps_decimals(session: Session) -> None:
    session.add(_iris(id_=42, species=Species.VIRGINICA))
    session.commit()
    session.expunge_all()

    row = session.scalars(select(Iris).where(Iris.id == 42)).one()

    assert row.sepal_length_cm == Decimal("5.1")
    assert isinstance(row.petal_width_cm, Decimal)
    assert row.species == "virginica"
    assert repr(row) == "Iris(id=42, species='virginica')"


def test_species_check_constraint_rejects_bad_value(session: Session) -> None:
    session.add(_iris(species="rose"))
    with pytest.raises(IntegrityError, match="CHECK constraint failed"):
        session.commit()


@pytest.mark.integration
def test_postgres_round_trip(pg_engine: Engine) -> None:
    factory = make_session_factory(pg_engine)
    with factory() as session:
        session.add(_iris(id_=1001, species=Species.VERSICOLOR))
        session.commit()
    with factory() as session:
        row = session.scalars(select(Iris).where(Iris.id == 1001)).one()
        assert row.sepal_width_cm == Decimal("3.5")
        session.execute(delete(Iris).where(Iris.id == 1001))
        session.commit()
