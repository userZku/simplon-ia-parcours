"""Train Pyrenex Crédit risk model — M1-B1.

Usage:
    python src/train.py --config default
    python src/train.py --config balanced
    python src/train.py --config gb_variant_a

Each run writes:
    models/pyrenex_risk_v2_<config>.joblib   (full Pipeline)
    models/pyrenex_risk_v2_<config>.json     (metadata, no holdout metric yet)

`gb_variant_a` also writes SHAP plots in `models/`:
    shap_bar_gb_variant_a.png
    shap_summary_gb_variant_a.png
"""
from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import sklearn
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from preprocess import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    TARGET_MAPPING,
    build_preprocessor,
    load_dataset,
)

CONFIGS: dict[str, dict] = {
    "default": {
        "estimator": "random_forest",
        "params": {
            "n_estimators": 100,
            "random_state": 42,
            "n_jobs": -1,
        },
    },
    "balanced": {
        "estimator": "random_forest",
        "params": {
            "n_estimators": 200,
            "max_depth": 10,
            "min_samples_leaf": 10,
            "class_weight": "balanced",
            "random_state": 42,
            "n_jobs": -1,
        },
    },
    "gb_variant_a": {
        "estimator": "gradient_boosting",
        "params": {
            "n_estimators": 250,
            "learning_rate": 0.05,
            "max_depth": 3,
            "subsample": 0.8,
            "random_state": 42,
        },
        "enable_shap": True,
    },
}


def _build_estimator(estimator_name: str, params: dict) -> RandomForestClassifier | GradientBoostingClassifier:
    if estimator_name == "random_forest":
        return RandomForestClassifier(**params)
    if estimator_name == "gradient_boosting":
        return GradientBoostingClassifier(**params)
    raise ValueError(f"Unknown estimator '{estimator_name}'")


def _save_shap_plots(
    pipeline: Pipeline,
    X_test,
    output_dir: Path,
    config_name: str,
    max_samples: int = 1000,
) -> list[str]:
    """Generate and save two SHAP plots for tree-based models."""
    try:
        import shap
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "SHAP is required for gb_variant_a. Install it with: pip install shap==0.46.0"
        ) from exc

    preprocessor = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["classifier"]

    X_test_proc = preprocessor.transform(X_test)
    feature_names = preprocessor.get_feature_names_out()
    X_shap = X_test_proc[:max_samples] if len(X_test_proc) > max_samples else X_test_proc

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_shap)

    if isinstance(shap_values, list):
        shap_values_plot = shap_values[1] if len(shap_values) > 1 else shap_values[0]
    else:
        shap_values_plot = shap_values

    output_dir.mkdir(parents=True, exist_ok=True)
    bar_path = output_dir / f"shap_bar_{config_name}.png"
    summary_path = output_dir / f"shap_summary_{config_name}.png"

    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_values_plot,
        X_shap,
        feature_names=feature_names,
        plot_type="bar",
        show=False,
    )
    plt.tight_layout()
    plt.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_values_plot,
        X_shap,
        feature_names=feature_names,
        show=False,
    )
    plt.tight_layout()
    plt.savefig(summary_path, dpi=150, bbox_inches="tight")
    plt.close()

    return [str(bar_path), str(summary_path)]


def train(config_name: str, data_path: Path, output_dir: Path) -> dict:
    if config_name not in CONFIGS:
        raise ValueError(f"Unknown config '{config_name}'. Available: {list(CONFIGS)}")

    config = CONFIGS[config_name]
    estimator_name = config["estimator"]
    params = config["params"]

    X, y = load_dataset(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            ("classifier", _build_estimator(estimator_name, params)),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_proba = pipeline.predict_proba(X_test)[:, 1]
    metrics = {
        "f1_macro": f1_score(y_test, pipeline.predict(X_test), average="macro"),
        "roc_auc": roc_auc_score(y_test, y_proba),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"pyrenex_risk_v2_{config_name}.joblib"
    joblib.dump(pipeline, model_path, compress=3)

    shap_plot_paths: list[str] = []
    if config.get("enable_shap", False):
        shap_plot_paths = _save_shap_plots(
            pipeline=pipeline,
            X_test=X_test,
            output_dir=output_dir,
            config_name=config_name,
        )

    meta = {
        "model_name": "pyrenex_risk_v2",
        "model_version": "v2.0.0",
        "config_name": config_name,
        "estimator": estimator_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "dataset_sha256": sha256(data_path.read_bytes()).hexdigest(),
        "metrics_holdout": None,
        "hyperparameters": params,
        "metrics_test_internal": {k: round(v, 4) for k, v in metrics.items()},
        "artifacts": {"shap_plots": shap_plot_paths},
        "feature_columns": {
            "numeric": list(NUMERIC_FEATURES),
            "categorical": list(CATEGORICAL_FEATURES),
        },
        "target": {"column": TARGET_COLUMN, "mapping": TARGET_MAPPING},
    }
    meta_path = output_dir / f"pyrenex_risk_v2_{config_name}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "model_path": model_path,
        "meta_path": meta_path,
        "metrics": metrics,
        "shap_plots": shap_plot_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Pyrenex risk model")
    parser.add_argument("--config", default="default", choices=list(CONFIGS))
    parser.add_argument("--data", default="data/lending_club_train.csv", type=Path)
    parser.add_argument("--output", default="models/", type=Path)
    args = parser.parse_args()

    result = train(args.config, args.data, args.output)
    print(f"Model saved to {result['model_path']}")
    print(f"Metadata saved to {result['meta_path']}")
    print(f"Metrics (test internal): {result['metrics']}")
    if result.get("shap_plots"):
        print(f"SHAP plots saved to: {result['shap_plots']}")
    print(
        "\nNext step: once you have chosen your retained config, promote it:\n"
        f"  cp {result['model_path']} {args.output}/pyrenex_risk_v2.joblib\n"
        f"  cp {result['meta_path']} {args.output}/pyrenex_risk_v2.json\n"
        "  python src/evaluate.py --update-meta"
    )


if __name__ == "__main__":
    main()