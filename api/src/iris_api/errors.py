"""Error handlers that render every error as the JSON envelope of the API contract."""

import logging

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger("iris_api")


def error_response(
    status: int, code: str, message: str, headers: list[tuple[str, str]] | None = None
) -> tuple[Response, int, list[tuple[str, str]]]:
    """Build ``{"error": {"code", "message"}}`` with ``status``."""
    return jsonify(error={"code": code, "message": message}), status, headers or []


def _handle_http_exception(exc: HTTPException) -> tuple[Response, int, list[tuple[str, str]]]:
    # Keep headers such as ``Allow`` on 405; the body's own Content-Type is replaced by JSON.
    headers = [(k, v) for k, v in exc.get_headers() if k.lower() != "content-type"]
    code = (exc.name or "error").lower().replace(" ", "_")  # "Not Found" -> "not_found"
    return error_response(exc.code or 500, code, exc.description or exc.name, headers)


def _handle_unexpected(exc: Exception) -> tuple[Response, int, list[tuple[str, str]]]:
    logger.exception("Unhandled error", exc_info=exc)
    return error_response(500, "internal_error", "Internal server error")


def register_error_handlers(app: Flask) -> None:
    """Register the JSON error handlers on ``app``."""
    app.register_error_handler(HTTPException, _handle_http_exception)
    app.register_error_handler(Exception, _handle_unexpected)
