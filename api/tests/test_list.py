import pytest
from flask.testing import FlaskClient


@pytest.mark.parametrize(
    ("species", "ids"), [("setosa", [1, 2, 3]), ("versicolor", [4, 5, 6]), ("virginica", [7, 8, 9])]
)
def test_list_returns_only_species_rows_ordered_by_id(
    client: FlaskClient, species: str, ids: list[int]
) -> None:
    response = client.get(f"/iris/{species}")

    assert response.status_code == 200
    body = response.get_json()
    assert [item["id"] for item in body["items"]] == ids
    assert {item["species"] for item in body["items"]} == {species}
    assert body["count"] == 3


def test_list_items_have_float_fields(client: FlaskClient) -> None:
    item = client.get("/iris/setosa").get_json()["items"][0]

    assert item == {
        "id": 1,
        "sepal_length_cm": 1.0,
        "sepal_width_cm": 1.1,
        "petal_length_cm": 1.2,
        "petal_width_cm": 1.3,
        "species": "setosa",
    }


def test_unknown_species_is_404(client: FlaskClient) -> None:
    response = client.get("/iris/rose")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "species_not_found"


def test_unknown_query_param_is_400_with_details(client: FlaskClient) -> None:
    response = client.get("/iris/setosa?foo=1")

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "invalid_query"
    assert error["details"] == [{"field": "foo", "message": "Extra inputs are not permitted"}]
