import pytest
from flask import Flask, abort
from flask.testing import FlaskClient


def test_unknown_route_is_404_envelope(client: FlaskClient) -> None:
    response = client.get("/nope")

    assert response.status_code == 404
    assert response.is_json
    body = response.get_json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]


def test_post_is_405_envelope_with_allow_header(client: FlaskClient) -> None:
    response = client.post("/health")

    assert response.status_code == 405
    assert response.is_json
    assert response.get_json()["error"]["code"] == "method_not_allowed"
    assert "GET" in response.headers["Allow"]


def test_bad_request_is_400_envelope(app: Flask) -> None:
    @app.get("/boom-400")
    def boom_400() -> str:
        abort(400, "bad input")

    response = app.test_client().get("/boom-400")

    assert response.status_code == 400
    assert response.get_json() == {"error": {"code": "bad_request", "message": "bad input"}}


def test_unexpected_exception_is_500_envelope_without_trace(
    app: Flask, caplog: pytest.LogCaptureFixture
) -> None:
    @app.get("/boom")
    def boom() -> str:
        raise RuntimeError("secret detail")

    response = app.test_client().get("/boom")

    assert response.status_code == 500
    assert response.get_json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }
    assert "secret detail" not in response.get_data(as_text=True)
    assert "Traceback" not in response.get_data(as_text=True)
    assert "secret detail" in caplog.text
