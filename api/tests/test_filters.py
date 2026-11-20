"""Filters of ``GET /iris/<species>``; setosa rows are ids 1-3 with increasing values."""

import pytest
from flask.testing import FlaskClient

# The value each column has on setosa row id 2 (see ``conftest.sample_rows``).
MIDDLE = {
    "id": "2",
    "sepal_length_cm": "1.1",
    "sepal_width_cm": "1.2",
    "petal_length_cm": "1.3",
    "petal_width_cm": "1.4",
}


def _ids(client: FlaskClient, query: str) -> list[int]:
    response = client.get(f"/iris/setosa?{query}")
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["count"] == len(body["items"])
    return [item["id"] for item in body["items"]]


@pytest.mark.parametrize("column", MIDDLE)
@pytest.mark.parametrize(
    ("template", "ids"),
    [
        ("{c}={v}", [2]),
        ("{c}_min={v}", [2, 3]),
        ("{c}_max={v}", [1, 2]),
        ("{c}_min={v}&{c}_max={v}", [2]),
    ],
    ids=["exact", "min", "max", "min+max"],
)
def test_filter_per_column(client: FlaskClient, column: str, template: str, ids: list[int]) -> None:
    assert _ids(client, template.format(c=column, v=MIDDLE[column])) == ids


def test_filters_on_different_columns_are_combined(client: FlaskClient) -> None:
    assert _ids(client, "sepal_length_cm_min=1.1&petal_width_cm_max=1.4") == [2]


def test_filter_without_match_returns_empty_list(client: FlaskClient) -> None:
    assert client.get("/iris/setosa?id=7").get_json() == {"items": [], "count": 0}


def test_trailing_zero_is_not_an_extra_decimal(client: FlaskClient) -> None:
    assert _ids(client, "sepal_length_cm=1.10") == [2]


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("foo=1", "foo"),
        ("id=abc", "id"),
        ("id_min=1.5", "id_min"),
        ("sepal_length_cm=abc", "sepal_length_cm"),
        ("petal_width_cm_max=nan", "petal_width_cm_max"),
        ("sepal_width_cm=1.15", "sepal_width_cm"),
        ("sepal_length_cm=1e200000", "sepal_length_cm"),
        ("petal_width_cm_min=100", "petal_width_cm_min"),
        ("id=", "id"),
        ("id=2147483648", "id"),
        ("id_min=-2147483649", "id_min"),
        ("id_max=99999999999999999999", "id_max"),
        ("sepal_width_cm_max=", "sepal_width_cm_max"),
        ("petal_length_cm_min=2&petal_length_cm_max=1", "query"),
    ],
    ids=[
        "unknown",
        "bad-int",
        "decimal-id",
        "bad-decimal",
        "nan",
        "too-many-decimals",
        "huge-exponent",
        "above-column-max",
        "empty-int",
        "id-above-int32",
        "id-below-int32",
        "id-above-int64",
        "empty-decimal",
        "min>max",
    ],
)
def test_invalid_filter_is_400(client: FlaskClient, query: str, field: str) -> None:
    response = client.get(f"/iris/setosa?{query}")

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "invalid_query"
    assert [detail["field"] for detail in error["details"]] == [field]


def test_min_above_max_names_both_params(client: FlaskClient) -> None:
    error = client.get("/iris/setosa?id_min=5&id_max=1").get_json()["error"]

    assert error["details"] == [
        {"field": "query", "message": "id_min must be less than or equal to id_max"}
    ]


def test_every_min_above_max_conflict_is_reported(client: FlaskClient) -> None:
    query = "id_min=5&id_max=1&sepal_length_cm_min=3&sepal_length_cm_max=1"
    error = client.get(f"/iris/setosa?{query}").get_json()["error"]

    assert [detail["message"] for detail in error["details"]] == [
        "id_min must be less than or equal to id_max",
        "sepal_length_cm_min must be less than or equal to sepal_length_cm_max",
    ]


def test_empty_value_says_so(client: FlaskClient) -> None:
    error = client.get("/iris/setosa?id=").get_json()["error"]

    assert error["details"] == [{"field": "id", "message": "Value must not be empty"}]


def test_repeated_param_is_400(client: FlaskClient) -> None:
    error = client.get("/iris/setosa?id_min=1&id_min=5").get_json()["error"]

    assert error["details"] == [{"field": "id_min", "message": "Parameter must not be repeated"}]


def test_id_filter_accepts_int32_bounds(client: FlaskClient) -> None:
    assert _ids(client, "id_min=-2147483648&id_max=2147483647") == [1, 2, 3]
