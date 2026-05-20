"""Schémas Pydantic v2 pour l'API de classification de sentiment."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


Sentiment = Literal["négatif", "neutre", "positif"]


class ReviewIn(BaseModel):
    """Payload d'entrée pour POST /predict.

    Une seule review FR à qualifier. La longueur max est contrôlée par
    `MAX_TEXT_LENGTH` (variable d'environnement, défaut 2000).
    """

    texte: str = Field(
        ...,
        min_length=1,
        description="Texte de la review en français (entre 1 et MAX_TEXT_LENGTH caractères).",
        examples=["Personnel charmant, chambre impeccable !"],
    )

    @field_validator("texte")
    @classmethod
    def texte_non_blanc(cls, v: str) -> str:
        """Refuse les chaînes composées uniquement d'espaces."""
        if not v.strip():
            raise ValueError("Le texte ne doit pas être vide ou composé uniquement d'espaces.")
        return v


class BatchIn(BaseModel):
    """Payload d'entrée pour POST /predict/batch.

    Permet d'analyser plusieurs reviews en une seule requête.
    """

    textes: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Liste de reviews FR (1 a 100 textes).",
        examples=[["Sejour agreable et equipe souriante.", "Chambre sale et bruyante."]],
    )

    @field_validator("textes")
    @classmethod
    def textes_non_vides(cls, values: list[str]) -> list[str]:
        """Refuse les elements vides ou composes uniquement d'espaces."""
        for i, value in enumerate(values):
            if not value or not value.strip():
                raise ValueError(f"Le texte a l'index {i} ne doit pas etre vide.")
        return values


class SentimentOut(BaseModel):
    """Réponse de POST /predict.

    Le sentiment est exprimé en 3 classes métier (négatif / neutre / positif),
    issues du mapping 5★ → 3 classes appliqué par `inference.predict_sentiment`.
    Les scores bruts du modèle (5 classes étoile) sont préservés pour la
    transparence.
    """

    sentiment: Sentiment = Field(..., description="Classe métier après mapping 5★ → 3 classes.")
    scores_5_stars: dict[str, float] = Field(
        ...,
        description="Probabilités brutes par étoile (somme ~= 1.0).",
        examples=[{"1 star": 0.04, "2 stars": 0.10, "3 stars": 0.20, "4 stars": 0.30, "5 stars": 0.36}],
    )
    model_name: str = Field(..., description="Identifiant HF du modèle utilisé.")
    latence_ms: float = Field(..., ge=0, description="Temps d'inférence côté serveur en millisecondes.")


class BatchOut(BaseModel):
    """Réponse de POST /predict/batch."""

    count: int = Field(..., ge=1, description="Nombre de reviews traitees.")
    predictions: list[SentimentOut] = Field(..., description="Resultats d'inference dans l'ordre des textes d'entree.")


class HealthOut(BaseModel):
    """Réponse de GET /health.

    Politique fail-fast : si l'API répond, le pipeline est chargé. Donc en
    pratique `status` vaut toujours `"ok"` et `model_loaded` vaut `True`.
    Si le pipeline est cassé, le conteneur a crashé au démarrage et on
    n'arrive pas ici (cf. `app/main.py:lifespan`).
    """

    status: Literal["ok"]
    model_loaded: bool


class InfoOut(BaseModel):
    """Réponse de GET /info — métadonnées du service."""

    service: str
    model_name: str
    native_classes: list[str] = Field(
        ...,
        description="Classes natives du modèle (avant mapping métier).",
        examples=[["1 star", "2 stars", "3 stars", "4 stars", "5 stars"]],
    )
    target_classes: list[str] = Field(
        ...,
        description="Classes cibles après mapping métier.",
        examples=[["négatif", "neutre", "positif"]],
    )
    max_text_length: int