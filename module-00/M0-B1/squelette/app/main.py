"""API FastAPI — service de classification de criticité (M0-B1).

Expose un modèle scikit-learn pré-entraîné (cf. `model/train_baseline.py`) via
deux routes :

- `GET /health`  : santé du service (déjà fonctionnel)
- `POST /predict` : prédiction de criticité (🎯 à compléter par l'apprenant)

Le modèle est chargé une seule fois au démarrage via le `lifespan` FastAPI puis
réutilisé pour chaque requête.

Lancement local :
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
import os
from typing import Any


import joblib
from fastapi import FastAPI, HTTPException
from loguru import logger
from pandas import DataFrame

from app.schemas import HealthResponse, MachineInput, PredictionResponse


MODEL_PATH = Path(__file__).resolve().parents[1] / "model" / "model.joblib"
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "api.log"

# Configuration Loguru : fichier + console
logger.remove()
logger.add(
    str(LOG_FILE),
    rotation="5 MB",
    retention="7 days",
    compression="zip",
    level="INFO",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)
logger.add(lambda msg: print(msg, end=""), colorize=True, level="INFO")

# Mémoire d'application — peuplée par le lifespan
state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Charge le modèle au démarrage, libère à l'arrêt.

    Args:
        app: instance FastAPI.
    """
    if not MODEL_PATH.is_file():
        logger.error(
            f"Modèle introuvable : {MODEL_PATH}. "
            f"Lance d'abord : python model/train_baseline.py"
        )
        raise RuntimeError(f"Modèle introuvable : {MODEL_PATH}")

    logger.info(f"Chargement du modèle depuis {MODEL_PATH}")
    state["model"] = joblib.load(MODEL_PATH)
    logger.info("Modèle chargé.")

    yield

    state.clear()
    logger.info("Service arrêté, état libéré.")


app = FastAPI(
    title="FastIA — Service de criticité maintenance prédictive",
    description=(
        "API d'exposition d'un modèle scikit-learn de classification de criticité "
        "d'incidents machine (3 classes : basse, moyenne, haute)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Retourne le statut du service et du modèle.

    Returns:
        HealthResponse — `status="ok"` si le modèle est chargé, `degraded` sinon.
    """
    is_loaded = "model" in state
    return HealthResponse(
        status="ok" if is_loaded else "degraded",
        model_loaded=is_loaded,
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(item: MachineInput) -> PredictionResponse:
    """Prédit la criticité d'une machine à partir de ses caractéristiques.

    🎯 **À COMPLÉTER PAR L'APPRENANT.**

    Indices d'implémentation :

    1. Construire un DataFrame pandas à 1 ligne à partir de `item.model_dump()`.
       Le pipeline scikit-learn attend les colonnes dans le même ordre qu'à
       l'entraînement (cf. `model/train_baseline.py`, `NUM_FEATURES` + `CAT_FEATURES`).
    2. Récupérer le modèle via `state["model"]`.
    3. Appeler `model.predict(df)[0]` pour obtenir la classe prédite (str).
    4. Appeler `model.predict_proba(df)[0]` pour obtenir les probabilités.
       Les classes correspondantes sont dans `model.classes_`.
    5. Construire et retourner un `PredictionResponse`.
    6. Logger l'entrée + la classe prédite + le temps de réponse via Loguru.

    Args:
        item: caractéristiques de la machine (cf. `schemas.MachineInput`).

    Returns:
        PredictionResponse avec la classe prédite et les probabilités.
    """
    logger.info("/predict - payload reçu: {}", item.model_dump())
    start = perf_counter()
    model = state.get("model")
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    try:
        # Une ligne d'entrée pour respecter le format attendu par scikit-learn.
        df = DataFrame([item.model_dump()])
        class_pred = model.predict(df)[0]
        proba = model.predict_proba(df)[0]
        classes = model.classes_
        proba_dict = {str(label): float(score) for label, score in zip(classes, proba)}

        response = PredictionResponse(
            criticite=str(class_pred),
            probabilites=proba_dict,
        )

        elapsed_ms = (perf_counter() - start) * 1000
        logger.info(
            "/predict - prédiction: {} | durée: {:.2f} ms",
            class_pred,
            elapsed_ms,
        )
        return response
    except HTTPException:
        raise
    except Exception:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.exception(
            "/predict - erreur | durée: {:.2f} ms",
            elapsed_ms,
        )
        raise HTTPException(status_code=500, detail="Erreur interne lors de la prédiction")
