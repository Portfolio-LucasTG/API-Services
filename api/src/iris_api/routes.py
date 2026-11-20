"""HTTP routes of the read-only API: parse -> query -> serialise, nothing else."""

import logging

from flask import Blueprint, request
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from iris_api.db import get_session
from iris_api.errors import ApiError
from iris_api.queries import build_list_query, build_retrieve_query
from iris_api.schemas import MAX_ID, IrisOut, ListQuery, ListResponse
from iris_common.models import Species

logger = logging.getLogger("iris_api")

bp = Blueprint("iris", __name__)


@bp.get("/health")
def health() -> tuple[dict[str, str], int]:
    """Report whether the database answers ``SELECT 1``."""
    try:
        get_session().execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Health check failed")
        return {"status": "unavailable"}, 503
    return {"status": "ok"}, 200


def _parse_species(value: str) -> Species:
    try:
        return Species(value)
    except ValueError:
        raise ApiError(404, "species_not_found", f"Unknown species: {value}") from None


def _parse_list_query() -> ListQuery:
    try:
        return ListQuery.model_validate(request.args.to_dict(flat=False))
    except ValidationError as exc:
        details = [
            # Model-level errors (min > max) have an empty ``loc``.
            {"field": ".".join(str(part) for part in err["loc"]) or "query", "message": err["msg"]}
            for err in exc.errors()
        ]
        raise ApiError(400, "invalid_query", "Invalid query parameters", details) from None


@bp.get("/iris/<species>")
def list_iris(species: str) -> dict[str, object]:
    """List the flowers of one species, ordered by id."""
    parsed_species, query = _parse_species(species), _parse_list_query()
    rows = get_session().scalars(build_list_query(parsed_species, query)).all()
    items = [IrisOut.model_validate(row) for row in rows]
    return ListResponse(items=items, count=len(items)).model_dump()


@bp.get(f"/iris/<species>/<int(max={MAX_ID}):id_>")
def retrieve_iris(species: str, id_: int) -> dict[str, object]:
    """Return one flower; 404 when it does not exist or belongs to another species."""
    row = get_session().scalars(build_retrieve_query(_parse_species(species), id_)).one_or_none()
    if row is None:
        raise ApiError(404, "not_found", f"No {species} iris with id {id_}")
    return IrisOut.model_validate(row).model_dump()
