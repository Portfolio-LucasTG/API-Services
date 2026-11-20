"""Error handlers that render every error as the JSON envelope of the API contract."""

import logging

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger("iris_api")

ErrorResult = tuple[Response, int, list[tuple[str, str]]]


class ApiError(Exception):
    """An expected client error (``species_not_found``, ``invalid_query``, ...)."""

    def __init__(
        self, status: int, code: str, message: str, details: list[dict[str, str]] | None = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


def error_response(
    status: int,
    code: str,
    message: str,
    headers: list[tuple[str, str]] | None = None,
    details: list[dict[str, str]] | None = None,
) -> ErrorResult:
    """Build ``{"error": {"code", "message", "details"?}}`` with ``status``."""
    error: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return jsonify(error=error), status, headers or []


def _handle_api_error(exc: ApiError) -> ErrorResult:
    return error_response(exc.status, exc.code, exc.message, details=exc.details)


def _handle_http_exception(exc: HTTPException) -> ErrorResult:
    # Keep headers such as ``Allow`` on 405; the body's own Content-Type is replaced by JSON.
    headers = [(k, v) for k, v in exc.get_headers() if k.lower() != "content-type"]
    code = (exc.name or "error").lower().replace(" ", "_")  # "Not Found" -> "not_found"
    return error_response(exc.code or 500, code, exc.description or exc.name, headers)


def _handle_unexpected(exc: Exception) -> ErrorResult:
    logger.exception("Unhandled error", exc_info=exc)
    return error_response(500, "internal_error", "Internal server error")


def register_error_handlers(app: Flask) -> None:
    """Register the JSON error handlers on ``app``."""
    app.register_error_handler(ApiError, _handle_api_error)
    app.register_error_handler(HTTPException, _handle_http_exception)
    app.register_error_handler(Exception, _handle_unexpected)
