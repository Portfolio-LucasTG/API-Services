"""Entry point of the ``iris-seed`` console script."""

import logging
from collections import Counter

from iris_common.db import make_engine
from iris_seeder.config import Settings
from iris_seeder.loader import upsert_rows
from iris_seeder.parsing import read_rows
from iris_seeder.source import resolve_dataset_path

logger = logging.getLogger("iris_seeder")


def run(settings: Settings) -> None:
    """Resolve, parse and upsert the dataset, then log a summary."""
    path = resolve_dataset_path(settings)
    rows = read_rows(path)
    logger.info("Read %d rows from %s", len(rows), path)
    engine = make_engine(settings.database_url)
    try:
        upserted = upsert_rows(engine, rows)
    finally:
        engine.dispose()
    per_species = Counter(row.species.value for row in rows)
    logger.info("Upserted %d rows; per species: %s", upserted, dict(sorted(per_species.items())))


def main() -> int:
    """Run the seeder and return the process exit code; never raises."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        settings = Settings()
        logging.getLogger().setLevel(settings.log_level.upper())
        run(settings)
    except Exception:
        logger.exception("Seeding failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
