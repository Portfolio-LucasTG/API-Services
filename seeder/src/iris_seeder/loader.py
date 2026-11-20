"""Write validated rows into PostgreSQL."""

from collections.abc import Sequence

from sqlalchemy import Engine, delete
from sqlalchemy.dialects.postgresql import insert

from iris_common.models import Base, Iris
from iris_seeder.parsing import IrisRow


def upsert_rows(engine: Engine, rows: Sequence[IrisRow]) -> int:
    """Create the table, then upsert ``rows`` by ``id`` and delete other ids, in one transaction.

    Returns the number of rows upserted.
    """
    Base.metadata.create_all(engine)
    # An empty file is more likely a broken download than an empty dataset: keep the table.
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
        connection.execute(delete(Iris).where(Iris.id.not_in([value["id"] for value in values])))
    return len(values)
