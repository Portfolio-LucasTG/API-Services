from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest

from iris_common.models import Species
from iris_seeder.parsing import DatasetParseError, read_rows
from iris_seeder.source import VENDORED_CSV

FIXTURES = Path(__file__).parent / "fixtures"


def test_small_file_maps_species_and_values() -> None:
    rows = read_rows(FIXTURES / "small.csv")

    assert Counter(row.species for row in rows) == dict.fromkeys(Species, 2)
    first = rows[0]
    assert (first.id, first.sepal_length_cm, first.petal_width_cm) == (
        1,
        Decimal("5.1"),
        Decimal("0.2"),
    )
    assert first.species is Species.SETOSA


@pytest.mark.parametrize(
    ("name", "line"),
    [("bad_number.csv", 3), ("bad_species.csv", 4), ("missing_column.csv", 1)],
)
def test_bad_file_error_names_line(name: str, line: int) -> None:
    with pytest.raises(DatasetParseError, match=rf"{name}:{line}:"):
        read_rows(FIXTURES / name)


def test_vendored_file_has_150_rows_50_per_species() -> None:
    rows = read_rows(VENDORED_CSV)

    assert len(rows) == 150
    assert Counter(row.species for row in rows) == dict.fromkeys(Species, 50)
