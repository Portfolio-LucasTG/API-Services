"""Pydantic models for API query parameters and responses."""

from pydantic import BaseModel, ConfigDict


class ListQuery(BaseModel):
    """Query parameters of ``GET /iris/<species>``; unknown params are rejected."""

    model_config = ConfigDict(extra="forbid")


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
