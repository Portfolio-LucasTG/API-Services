"""Pagination of ``GET /iris/<species>``; setosa rows are ids 1-3."""

import pytest
from flask.testing import FlaskClient


def _page(client: FlaskClient, query: str) -> dict[str, object]:
    response = client.get(f"/iris/setosa?{query}")
    assert response.status_code == 200, response.get_json()
    body: dict[str, object] = response.get_json()
    return body


def _ids(body: dict[str, object]) -> list[int]:
    items = body["items"]
    assert isinstance(items, list)
    return [item["id"] for item in items]


def test_no_pagination_params_keep_list_shape(client: FlaskClient) -> None:
    assert _page(client, "").keys() == {"items", "count"}


def test_page_only_uses_default_per_page(client: FlaskClient) -> None:
    body = _page(client, "page=1")

    assert {k: v for k, v in body.items() if k != "items"} == {
        "page": 1,
        "per_page": 10,
        "total": 3,
        "pages": 1,
    }
    assert _ids(body) == [1, 2, 3]


@pytest.mark.parametrize(
    ("query", "page", "ids"),
    [("per_page=2", 1, [1, 2]), ("per_page=2&page=2", 2, [3]), ("per_page=2&page=3", 3, [])],
    ids=["first-page-default", "last-partial-page", "past-the-end"],
)
def test_per_page_math(client: FlaskClient, query: str, page: int, ids: list[int]) -> None:
    body = _page(client, query)

    assert (body["page"], body["per_page"], body["total"], body["pages"]) == (page, 2, 3, 2)
    assert _ids(body) == ids


def test_pagination_with_filters_counts_filtered_rows(client: FlaskClient) -> None:
    body = _page(client, "id_min=2&per_page=1&page=2")

    assert (body["total"], body["pages"]) == (2, 2)
    assert _ids(body) == [3]


def test_largest_page_is_empty_not_an_error(client: FlaskClient) -> None:
    body = _page(client, "page=2147483647&per_page=100")

    assert (body["items"], body["page"], body["total"]) == ([], 2147483647, 3)


def test_no_match_has_zero_pages(client: FlaskClient) -> None:
    body = _page(client, "id=7&page=1")

    assert (body["items"], body["total"], body["pages"]) == ([], 0, 0)


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("per_page=0", "per_page"),
        ("per_page=101", "per_page"),
        ("page=0", "page"),
        ("page=abc", "page"),
        ("page=", "page"),
        ("page=2147483648", "page"),
        ("page=1&page=2", "page"),
        ("per_page=2&per_page=3", "per_page"),
    ],
)
def test_invalid_pagination_is_400(client: FlaskClient, query: str, field: str) -> None:
    response = client.get(f"/iris/setosa?{query}")

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "invalid_query"
    assert [detail["field"] for detail in error["details"]] == [field]
    assert "supported_params" not in error


def test_unknown_param_lists_supported_params(client: FlaskClient) -> None:
    error = client.get("/iris/setosa?foo=1").get_json()["error"]
    params = error["supported_params"]

    assert params["id_min"] == {"type": "integer", "minimum": -(2**31), "maximum": 2**31 - 1}
    assert params["sepal_length_cm"] == {
        "type": "number",
        "format": "float",
        "decimal_places": 1,
    }
    assert params["page"] == {"type": "integer", "minimum": 1, "maximum": 2**31 - 1, "default": 1}
    assert params["per_page"] == {"type": "integer", "minimum": 1, "maximum": 100, "default": 10}
    assert len(params) == 17  # 5 columns x 3 filters + page + per_page
