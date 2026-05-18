from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Fixture client module : ouvre TestClient(app) avec lifespan."""
    with TestClient(app) as test_client:
        yield test_client


def _valid_payload() -> dict:
    return {
        "type_machine": "compresseur",
        "age_machine_jours": 1500,
        "derniere_maintenance_jours": 45,
        "temperature_moyenne": 68.5,
        "vibration_moyenne": 3.2,
        "pression_moyenne": 7.8,
        "nb_incidents_3_mois": 2,
    }


def test_predict_returns_200_with_expected_schema() -> None:
    with TestClient(app) as client:
        response = client.post("/predict", json=_valid_payload())

    assert response.status_code == 200
    body = response.json()

    assert set(body.keys()) == {"criticite", "probabilites"}
    assert body["criticite"] in {"basse", "moyenne", "haute"}
    assert set(body["probabilites"].keys()) == {"basse", "moyenne", "haute"}


def test_predict_returns_422_for_invalid_payload() -> None:
    invalid_payload = _valid_payload()
    invalid_payload["nb_incidents_3_mois"] = -1

    with TestClient(app) as client:
        response = client.post("/predict", json=invalid_payload)

    assert response.status_code == 422


def test_predict_valid_case_with_probabilities(client) -> None:
    """Test cas valide : 200 + criticite + somme proba ≈ 1."""
    payload = _valid_payload()
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["criticite"] in {"basse", "moyenne", "haute"}

    # Somme des probabilités ≈ 1.0 (avec tolérance 1e-6)
    total_proba = sum(body["probabilites"].values())
    assert abs(total_proba - 1.0) < 1e-6


def test_predict_invalid_type_machine_unknown(client) -> None:
    """Test cas invalide : type_machine inconnu → 422."""
    invalid_payload = _valid_payload()
    invalid_payload["type_machine"] = "INCONNU"
    response = client.post("/predict", json=invalid_payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "type_machine",
    ["pompe", "convoyeur", "presse", "four"],
)
def test_predict_parametrized_machine_types(client, type_machine: str) -> None:
    """Test paramétré : 4 types machines doivent renvoyer 200."""
    payload = _valid_payload()
    payload["type_machine"] = type_machine
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["criticite"] in {"basse", "moyenne", "haute"}
    assert set(body["probabilites"].keys()) == {"basse", "moyenne", "haute"}
