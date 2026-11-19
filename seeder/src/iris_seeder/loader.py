"""Write validated rows into PostgreSQL."""

from collections.abc import Sequence

from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from iris_common.models import Base, Iris
from iris_seeder.parsing import IrisRow


def upsert_rows(engine: Engine, rows: Sequence[IrisRow]) -> int:
    """Create the table if needed and upsert ``rows`` by ``id`` in one transaction."""
    Base.metadata.create_all(engine)
    if not rows:
        return 0
    # .value: psycopg would otherwise adapt the StrEnum by its member name
    values = [{**row.model_dump(exclude={"species"}), "species": row.species.value} for row in rows]
    stmt = insert(Iris).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Iris.id],
        set_={column: stmt.excluded[column] for column in values[0] if column != "id"},
    )
    with engine.begin() as connection:
        connection.execute(stmt)
    return len(values)
