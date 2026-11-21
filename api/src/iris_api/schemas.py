"""Pydantic models for API query parameters and responses."""

import functools
import math
from decimal import Decimal
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import InitErrorDetails, PydanticCustomError, core_schema

# Columns that accept ``<column>``, ``<column>_min`` and ``<column>_max`` filters.
FILTER_COLUMNS = ("id", "sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm")

# Same bounds as the ``Numeric(3, 1)`` columns, so huge values are a 400 and never reach the DB.
# ``Iris.id`` is a 32-bit INTEGER in PostgreSQL; ids outside that range can't exist.
MAX_ID = 2**31 - 1
Id = Annotated[int, Field(ge=-MAX_ID - 1, le=MAX_ID)]

Measure = Annotated[Decimal, Field(max_digits=3, decimal_places=1)]

PAGINATION_PARAMS = frozenset({"page", "per_page"})


class ListQuery(BaseModel):
    """Query parameters of ``GET /iris/<species>``; unknown params are rejected."""

    model_config = ConfigDict(extra="forbid")

    id: Id | None = None
    id_min: Id | None = None
    id_max: Id | None = None
    sepal_length_cm: Measure | None = None
    sepal_length_cm_min: Measure | None = None
    sepal_length_cm_max: Measure | None = None
    sepal_width_cm: Measure | None = None
    sepal_width_cm_min: Measure | None = None
    sepal_width_cm_max: Measure | None = None
    petal_length_cm: Measure | None = None
    petal_length_cm_min: Measure | None = None
    petal_length_cm_max: Measure | None = None
    petal_width_cm: Measure | None = None
    petal_width_cm_min: Measure | None = None
    petal_width_cm_max: Measure | None = None
    # Capped at MAX_ID so the OFFSET stays far inside PostgreSQL's BIGINT.
    page: int = Field(1, ge=1, le=MAX_ID)
    per_page: int = Field(10, ge=1, le=100)

    @property
    def paginated(self) -> bool:
        """Pagination is opt-in: on only when ``page`` or ``per_page`` was sent."""
        return bool(PAGINATION_PARAMS & self.model_fields_set)

    @field_validator("*", mode="before")
    @classmethod
    def _single_non_empty(cls, value: object) -> object:
        # Query args arrive as lists (``to_dict(flat=False)``) so a repeated param is caught.
        match value:
            case [_, _, *_]:
                raise PydanticCustomError("repeated", "Parameter must not be repeated")
            case [single]:
                value = single
        if value == "":
            raise PydanticCustomError("empty", "Value must not be empty")
        return value

    @model_validator(mode="after")
    def _min_not_above_max(self) -> Self:
        errors: list[InitErrorDetails] = []
        for column in FILTER_COLUMNS:
            low, high = getattr(self, f"{column}_min"), getattr(self, f"{column}_max")
            if low is not None and high is not None and low > high:
                message = f"{column}_min must be less than or equal to {column}_max"
                errors.append(
                    {
                        "type": PydanticCustomError("min_above_max", message),
                        "loc": (),
                        "input": {f"{column}_min": low, f"{column}_max": high},
                    }
                )
        if errors:
            # A ValidationError (not ValueError) keeps one entry per conflicting column.
            raise ValidationError.from_exception_data(type(self).__name__, errors)
        return self


class IrisOut(BaseModel):
    """One flower; ``Numeric`` columns are serialised as JSON numbers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sepal_length_cm: float
    sepal_width_cm: float
    petal_length_cm: float
    petal_width_cm: float
    species: str


class ListResponse(BaseModel):
    """Unpaginated list response."""

    items: list[IrisOut]
    count: int


class PageResponse(BaseModel):
    """Paginated list response; ``total`` and ``pages`` reflect the filters."""

    items: list[IrisOut]
    page: int
    per_page: int
    total: int

    @computed_field  # type: ignore[prop-decorator]  # mypy can't type a decorated property
    @property
    def pages(self) -> int:
        """Number of pages for ``total`` rows."""
        return math.ceil(self.total / self.per_page)


class _ParamsSchema(GenerateJsonSchema):
    """JSON schema of query params as a client sees them: plain numbers, no ``null`` option."""

    def decimal_schema(self, schema: core_schema.DecimalSchema) -> JsonSchemaValue:
        value: JsonSchemaValue = {"type": "number", "format": "float"}
        if (places := schema.get("decimal_places")) is not None:
            value["decimal_places"] = places
        return value

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        return self.generate_inner(schema["schema"])


@functools.cache  # the schema never changes; callers must not mutate the result
def supported_params() -> dict[str, JsonSchemaValue]:
    """Map each query param of ``ListQuery`` to its type and allowed values."""
    properties: dict[str, JsonSchemaValue] = ListQuery.model_json_schema(
        schema_generator=_ParamsSchema
    )["properties"]
    return {
        name: {k: v for k, v in prop.items() if k != "title" and not (k == "default" and v is None)}
        for name, prop in properties.items()
    }
