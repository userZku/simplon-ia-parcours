"""Pyrenex Risk API — entry point.

TODO — Complete the routes /info and /predict.
"""
from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from app.middleware import LoggingMiddleware
from app.schemas import HealthResponse, LoanApplication, Prediction

# --- Loguru configuration ---------------------------------------------------

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stderr, level="INFO", colorize=True)
logger.add(
    LOGS_DIR / "api.log",
    rotation="10 MB",
    retention="7 days",
    compression="gz",
    serialize=True,
    enqueue=True,
    level="INFO",
)


# --- Lifespan ---------------------------------------------------------------

MODELS_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODELS_DIR / "pyrenex_risk_v2.joblib"
META_PATH = MODELS_DIR / "pyrenex_risk_v2.json"
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Bearer token placeholder for M5. Not enforced yet.",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model + metadata at startup, release at shutdown."""
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model file not found at {MODEL_PATH}")
    if not META_PATH.exists():
        raise RuntimeError(f"Metadata file not found at {META_PATH}")

    app.state.model = joblib.load(MODEL_PATH)
    app.state.metadata = json.loads(META_PATH.read_text(encoding="utf-8"))
    logger.info(
        "Model loaded: {name} {version}",
        name=app.state.metadata["model_name"],
        version=app.state.metadata["model_version"],
    )
    yield
    app.state.model = None
    logger.info("Model released")


app = FastAPI(
    title="Pyrenex Risk API",
    version="0.1.0",
    description="API serving the Pyrenex Crédit credit-risk scoring model.",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(LoggingMiddleware)


# --- Routes -----------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness check."""
    if not hasattr(app.state, "model") or app.state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return HealthResponse(status="ok")


@app.get("/info")
async def info() -> dict:
    """Return loaded model metadata."""
    if not hasattr(app.state, "metadata"):
        raise HTTPException(status_code=503, detail="Model metadata not loaded")

    metadata = app.state.metadata
    return {
        "api_version": app.version,
        "model_name": metadata["model_name"],
        "model_version": metadata["model_version"],
        "model_created_at": metadata["created_at"],
        "metrics_holdout": metadata.get("metrics_holdout", {}),
    }


@app.post(
    "/predict",
    response_model=Prediction,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"description": "Invalid input payload"},
        500: {"description": "Model inference failed"},
        503: {"description": "Model not loaded"},
    },
)
async def predict(
    application: LoanApplication,
    request: Request,
    bearer_credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> Prediction:
    """Predict default risk for one loan application."""
    model = getattr(app.state, "model", None)
    metadata = getattr(app.state, "metadata", None)

    if model is None or metadata is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        x_input = pd.DataFrame([application.model_dump()])
        prediction = int(model.predict(x_input)[0])
        probability = float(model.predict_proba(x_input)[0, 1])
    except Exception as exc:
        logger.bind(request_id=getattr(request.state, "request_id", None)).exception(
            "Model inference failed"
        )
        raise HTTPException(status_code=500, detail="Model inference failed") from exc

    return Prediction(
        prediction=prediction,
        probability=probability,
        model_version=metadata["model_version"],
        request_id=getattr(request.state, "request_id", ""),
    )
