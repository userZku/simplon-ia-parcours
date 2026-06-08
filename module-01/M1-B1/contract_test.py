"""Contract test du modèle Pyrenex-risk-v2 — à compléter.

Ce script valide que le `.joblib` packagé respecte la signature attendue
par l'API M1-B2. Plus exigeant qu'un simple `print OK` : on vérifie
shapes, classes, bornes des probas, et stabilité prédictive vs notebook.

Mini-cours d'appui : `ressources/05_Persistance_modele_joblib_essentiel.md`
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).parent / "models" / "pyrenex_risk_v2.joblib"


def contract_test_model(
    model_path: Path,
    x_sample: pd.DataFrame,
    expected_classes: set[int] | None = None,
    expected_first_proba: list[float] | None = None,
) -> None:
    """Valide schéma + stabilité prédictive d'un modèle rechargé.

    Args:
        model_path: chemin vers le `.joblib` à valider.
        x_sample: DataFrame d'au moins 3 lignes aligné sur `feature_columns`.
        expected_classes: classes attendues (ex. ``{0, 1}``).
        expected_first_proba: probabilités attendues pour la 1re ligne,
            issues d'une référence notebook.
    """
    pipeline = joblib.load(model_path)
    # For bit-level reproducibility, force deterministic single-thread inference.
    if hasattr(pipeline.named_steps["classifier"], "set_params"):
        pipeline.named_steps["classifier"].set_params(n_jobs=1)
    prediction = pipeline.predict(x_sample.head(3))
    proba = pipeline.predict_proba(x_sample.head(3))

    assert prediction.shape == (3,), f"shape predict={prediction.shape}, attendu (3,)"
    assert proba.shape == (3, 2), f"shape predict_proba={proba.shape}, attendu (3, 2)"
    assert (proba >= 0).all() and (proba <= 1).all(), "probabilités hors [0, 1]"

    if expected_classes is not None:
        observed = set(prediction.tolist())
        assert observed <= expected_classes, (
            f"classes inattendues : {observed - expected_classes}"
        )

    if expected_first_proba is not None:
        observed = proba[0].round(6).tolist()
        reference = [round(p, 6) for p in expected_first_proba]
        assert observed == reference, (
            f"dérive prédictive — observé {observed}, référence notebook {reference}"
        )

    print("Contract test OK — shapes valides, probas dans [0,1], stabilité confirmée.")


if __name__ == "__main__":
    # Référence capturée depuis le notebook de rendu (même modèle final).
    expected_predictions = [0, 1, 0]
    expected_proba = np.array(
        [
            [0.7701772162545066, 0.22982278374549156],
            [0.38946389260121883, 0.6105361073987795],
            [0.6780244736257308, 0.3219755263742687],
        ],
        dtype=np.float64,
    )

    x_holdout = pd.read_csv(
        Path(__file__).parent / "data" / "lending_club_holdout.csv"
    ).drop(columns=["loan_status"])

    pipeline = joblib.load(MODEL_PATH)
    pipeline.named_steps["classifier"].set_params(n_jobs=1)
    observed_predictions = pipeline.predict(x_holdout.head(3)).tolist()
    observed_proba = pipeline.predict_proba(x_holdout.head(3))

    assert observed_predictions == expected_predictions, (
        "dérive prédictive — classes observées "
        f"{observed_predictions}, référence notebook {expected_predictions}"
    )
    assert np.array_equal(observed_proba, expected_proba), (
        "dérive bit-à-bit — probabilités différentes de la référence notebook"
    )

    contract_test_model(
        MODEL_PATH,
        x_sample=x_holdout,
        expected_classes={0, 1},
        expected_first_proba=expected_proba[0].tolist(),
    )