from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typing import Iterator

from app.main import MAX_TEXT_LENGTH, app, state
from app.schemas import SentimentOut


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def _mock_predict_sentiment(monkeypatch):
    state["pipeline"] = object()

    def fake_predict_sentiment(pipeline, text: str, model_name: str) -> SentimentOut:
        return SentimentOut(
            sentiment="positif",
            scores_5_stars={
                "1 star": 0.01,
                "2 stars": 0.04,
                "3 stars": 0.10,
                "4 stars": 0.25,
                "5 stars": 0.60,
            },
            model_name=model_name,
            latence_ms=12.3,
        )

    monkeypatch.setattr("app.main.inference.predict_sentiment", fake_predict_sentiment)


def _valid_payload() -> dict[str, str]:
    return {"texte": "Service excellent, je recommande."}


def test_predict_returns_200_with_expected_schema(client: TestClient) -> None:
    response = client.post("/predict", json=_valid_payload())

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"sentiment", "scores_5_stars", "model_name", "latence_ms"}
    assert body["sentiment"] in {"négatif", "neutre", "positif"}
    assert set(body["scores_5_stars"].keys()) == {
        "1 star",
        "2 stars",
        "3 stars",
        "4 stars",
        "5 stars",
    }


def test_predict_returns_422_for_too_long_text(client: TestClient) -> None:
    payload = {"texte": "a" * (MAX_TEXT_LENGTH + 1)}
    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    assert "Texte trop long" in response.json()["detail"]


def test_predict_returns_422_for_blank_text(client: TestClient) -> None:
    response = client.post("/predict", json={"texte": "   "})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("ne doit pas être vide" in err["msg"] for err in detail)
