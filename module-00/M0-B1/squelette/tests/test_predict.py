from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


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
