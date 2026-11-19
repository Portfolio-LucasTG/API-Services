"""SQLAlchemy model for the Iris dataset."""

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all tables."""


class Species(StrEnum):
    """The three Iris species, as stored in the database and used in URLs."""

    SETOSA = "setosa"
    VERSICOLOR = "versicolor"
    VIRGINICA = "virginica"


_SPECIES_SQL_LIST = ", ".join(f"'{species.value}'" for species in Species)


class Iris(Base):
    """One measured flower. ``id`` comes from the CSV, so it is not autoincremented."""

    __tablename__ = "iris"
    __table_args__ = (CheckConstraint(f"species IN ({_SPECIES_SQL_LIST})", name="ck_iris_species"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    sepal_length_cm: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    sepal_width_cm: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    petal_length_cm: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    petal_width_cm: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    species: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Iris(id={self.id!r}, species={self.species!r})"
