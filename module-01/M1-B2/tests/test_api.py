"""M1-B2 — API tests.

3 tests required (health, predict valid, predict invalid).
Bonus tests welcome (deterministic, info schema, etc.).
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok(client: TestClient) -> None:
    """/health returns 200 and the expected status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_503_when_model_not_loaded(client: TestClient) -> None:
    """/health returns 503 when model is temporarily unavailable."""
    original_model = app.state.model
    app.state.model = None
    try:
        response = client.get("/health")
    finally:
        app.state.model = original_model

    assert response.status_code == 503
    assert response.json() == {"detail": "Model not loaded"}


def test_predict_valid_payload(client: TestClient, valid_payload: dict) -> None:
    """/predict returns 200 with a well-formed response on valid input."""
    response = client.post("/predict", json=valid_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in (0, 1)
    assert 0.0 <= data["probability"] <= 1.0
    assert "request_id" in data
    assert data["model_version"] == "v2.0.0"


def test_predict_missing_field_returns_422(
    client: TestClient, valid_payload: dict
) -> None:
    """/predict returns 422 on missing required field."""
    invalid = {k: v for k, v in valid_payload.items() if k != "loan_amnt"}
    response = client.post("/predict", json=invalid)
    assert response.status_code == 422
    assert "loan_amnt" in response.text


def test_info_exposes_mandatory_non_null_keys(client: TestClient) -> None:
    """/info exposes required keys and all returned values are non-null."""
    response = client.get("/info")
    assert response.status_code == 200

    data = response.json()
    required_keys = {
        "api_version",
        "model_name",
        "model_version",
        "model_created_at",
        "metrics_holdout",
    }

    assert required_keys.issubset(data.keys())
    for key in required_keys:
        assert data[key] is not None


# TODO — Add at least one bonus test (e.g. test_predict_is_deterministic)
