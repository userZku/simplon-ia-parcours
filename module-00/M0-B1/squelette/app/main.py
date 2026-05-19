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
from json import JSONDecodeError
from pathlib import Path
from time import perf_counter
import os
from typing import Any


import httpx
import joblib
from fastapi import FastAPI, HTTPException
from loguru import logger
from pandas import DataFrame

from app.schemas import ExplainResponse, HealthResponse, MachineInput, PredictionResponse


MODEL_PATH = Path(__file__).resolve().parents[1] / "model" / "model.joblib"
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "api.log"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
PREDICT_URL = os.getenv("PREDICT_URL", "http://127.0.0.1:8000/predict")
PREDICT_HTTP_TIMEOUT = httpx.Timeout(20.0)
# Ollama peut mettre plusieurs minutes selon le modèle et la machine.
# On garde un connect timeout court mais pas de read timeout.
OLLAMA_HTTP_TIMEOUT = httpx.Timeout(connect=10.0, read=None, write=60.0, pool=10.0)

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
        p_basse = proba_dict.get("basse")
        p_moyenne = proba_dict.get("moyenne")
        p_haute = proba_dict.get("haute")
        logger.info(
            "/predict - prédiction: {} | proba_basse={} | proba_moyenne={} | proba_haute={} | durée: {:.2f} ms",
            class_pred,
            p_basse,
            p_moyenne,
            p_haute,
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


@app.post("/explain", response_model=ExplainResponse)
def explain(item: MachineInput) -> ExplainResponse:
    """Explique en français la prédiction de criticité via un LLM local Ollama."""
    logger.info("/explain - payload reçu: {}", item.model_dump())
    start = perf_counter()

    try:
        with httpx.Client(timeout=PREDICT_HTTP_TIMEOUT) as client:
            predict_resp = client.post(PREDICT_URL, json=item.model_dump())
        predict_resp.raise_for_status()
        pred_json = predict_resp.json()

        class_pred = str(pred_json.get("criticite", ""))
        proba_dict = pred_json.get("probabilites", {})

        if not class_pred or not isinstance(proba_dict, dict):
            raise HTTPException(status_code=502, detail="Réponse invalide de /predict")

        prompt = (
            "Tu es un assistant d'explication de prédictions en maintenance prédictive. "
            "Rédige uniquement en français, en 2 à 3 phrases maximum, avec un style simple et non technique. "
            "Explique la criticité prédite en t'appuyant sur les caractéristiques de la machine et les probabilités fournies, sans inventer d'informations."
            "Termine toujours par une phrase complète avec un point final.\n\n"
            f"Payload: {item.model_dump()}\n"
            f"Criticité prédite: {class_pred}\n"
            f"Probabilités: {proba_dict}\n"
        )

        with httpx.Client(timeout=OLLAMA_HTTP_TIMEOUT) as client:
            ollama_resp = client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 160,
                        "num_ctx": 1024,
                        "temperature": 0.3,
                        "num_thread": 8
                    },
                },
            )
        ollama_resp.raise_for_status()
        data = ollama_resp.json()
        explanation = str(data.get("response", "")).strip()

        if not explanation:
            raise HTTPException(status_code=502, detail="Réponse vide de Ollama")

        elapsed_ms = (perf_counter() - start) * 1000
        logger.info(
            "/explain - prédiction: {} | modèle_llm: {} | durée: {:.2f} ms",
            class_pred,
            OLLAMA_MODEL,
            elapsed_ms,
        )
        return ExplainResponse(
            criticite=class_pred,
            probabilites=proba_dict,
            explication=explanation,
            modele_llm=OLLAMA_MODEL,
        )
    except HTTPException:
        raise
    except (httpx.HTTPError, JSONDecodeError):
        logger.exception("/explain - erreur de communication avec /predict ou Ollama")
        raise HTTPException(status_code=503, detail="Service dépendant indisponible (/predict ou Ollama)")
    except Exception:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.exception(
            "/explain - erreur | durée: {:.2f} ms",
            elapsed_ms,
        )
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'explication")

