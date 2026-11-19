"""Parse and validate the Iris CSV."""

import csv
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from iris_common.models import Species

Measure = Annotated[Decimal, Field(gt=0, max_digits=3, decimal_places=1)]

CSV_COLUMNS = ("Id", "SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm", "Species")


class DatasetParseError(ValueError):
    """The CSV is malformed; the message names the offending line."""


class IrisRow(BaseModel):
    """One validated CSV row, with field names matching ``iris_common.models.Iris``."""

    model_config = ConfigDict(frozen=True)

    id: int = Field(alias="Id", gt=0)
    sepal_length_cm: Measure = Field(alias="SepalLengthCm")
    sepal_width_cm: Measure = Field(alias="SepalWidthCm")
    petal_length_cm: Measure = Field(alias="PetalLengthCm")
    petal_width_cm: Measure = Field(alias="PetalWidthCm")
    species: Species = Field(alias="Species")

    @field_validator("species", mode="before")
    @classmethod
    def _strip_iris_prefix(cls, value: object) -> object:
        """Map ``Iris-setosa`` to ``setosa``; anything else is checked against ``Species``."""
        return value.removeprefix("Iris-") if isinstance(value, str) else value


def read_rows(path: Path) -> list[IrisRow]:
    """Read every row of ``path``; raise ``DatasetParseError`` on the first invalid one."""
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = [column for column in CSV_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise DatasetParseError(f"{path}:1: missing column(s) {', '.join(missing)}")
        rows = []
        for line, record in enumerate(reader, start=2):
            try:
                rows.append(IrisRow.model_validate(record))
            except ValidationError as exc:
                raise DatasetParseError(f"{path}:{line}: {exc}") from exc
    return rows
