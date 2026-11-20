from flask.testing import FlaskClient


def test_retrieve_returns_item(client: FlaskClient) -> None:
    response = client.get("/iris/virginica/8")

    assert response.status_code == 200
    assert response.get_json() == {
        "id": 8,
        "sepal_length_cm": 3.1,
        "sepal_width_cm": 3.2,
        "petal_length_cm": 3.3,
        "petal_width_cm": 3.4,
        "species": "virginica",
    }


def test_retrieve_id_of_other_species_is_404(client: FlaskClient) -> None:
    response = client.get("/iris/setosa/8")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_retrieve_nonexistent_id_is_404(client: FlaskClient) -> None:
    response = client.get("/iris/setosa/999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_retrieve_unknown_species_is_404(client: FlaskClient) -> None:
    response = client.get("/iris/rose/1")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "species_not_found"


def test_retrieve_id_beyond_int_range_is_404(client: FlaskClient) -> None:
    response = client.get("/iris/setosa/99999999999999999999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
