from __future__ import annotations

import pytest

from app.inference import map_stars_to_sentiment, predict_sentiment


class FakePipeline:
    def __call__(self, text: str, top_k=None):
        assert isinstance(text, str)
        assert top_k is None
        return [
            {"label": "1 star", "score": 0.05},
            {"label": "2 stars", "score": 0.10},
            {"label": "3 stars", "score": 0.15},
            {"label": "4 stars", "score": 0.20},
            {"label": "5 stars", "score": 0.50},
        ]


def test_map_stars_to_sentiment_happy_path() -> None:
    assert map_stars_to_sentiment("1 star") == "négatif"
    assert map_stars_to_sentiment("3 stars") == "neutre"
    assert map_stars_to_sentiment("5 stars") == "positif"


def test_map_stars_to_sentiment_raises_on_unknown_label() -> None:
    with pytest.raises(ValueError):
        map_stars_to_sentiment("6 stars")


def test_predict_sentiment_returns_expected_payload() -> None:
    result = predict_sentiment(
        pipeline=FakePipeline(),
        text="Très bon séjour, équipe super agréable.",
        model_name="fake/model",
    )

    assert result.sentiment == "positif"
    assert result.model_name == "fake/model"
    assert result.latence_ms >= 0
    assert set(result.scores_5_stars.keys()) == {
        "1 star",
        "2 stars",
        "3 stars",
        "4 stars",
        "5 stars",
    }


def test_predict_sentiment_uses_highest_score_for_mapping() -> None:
    class NegativePipeline:
        def __call__(self, text: str, top_k=None):
            return [
                {"label": "1 star", "score": 0.70},
                {"label": "2 stars", "score": 0.20},
                {"label": "3 stars", "score": 0.05},
                {"label": "4 stars", "score": 0.03},
                {"label": "5 stars", "score": 0.02},
            ]

    result = predict_sentiment(
        pipeline=NegativePipeline(),
        text="Expérience très décevante.",
        model_name="fake/model",
    )

    assert result.sentiment == "négatif"
