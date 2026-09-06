"""Ensemble meta-classifier: trains logistic regression on per-member predictions.

Must be run AFTER evaluate.py produces per-member prediction CSVs.
Uses ONLY validation + training predictions (never test).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.config import load_config, resolve_path
from ml.evaluation.metrics import compute_all_metrics

logger = logging.getLogger("voxshield.training.ensemble")


def fit_logistic_regression(
    predictions_csv: Path,
    output_path: Path,
    member_names: list[str] | None = None,
):
    """Fit a logistic regression meta-classifier on member model predictions.

    Only uses train + validation data. Test data is held out.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score

    df = pd.read_csv(predictions_csv)

    if member_names is None:
        member_cols = [c for c in df.columns if c.startswith("p_fake_")]
        member_names = [c.replace("p_fake_", "") for c in member_cols]
    else:
        member_cols = [f"p_fake_{m}" for m in member_names]

    # Only train + validation
    train_val = df[df["split"].isin(["train", "validation"])].copy()
    test = df[df["split"] == "test"].copy()

    if len(train_val) == 0:
        logger.error("No train/validation samples in predictions CSV")
        return

    X_train = train_val[member_cols].values
    y_train = train_val["label"].values

    # Fit
    clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
    clf.fit(X_train, y_train)

    # Cross-validation score
    cv_scores = cross_val_score(clf, X_train, y_train, cv=5, scoring="f1")
    logger.info("CV F1: %.4f (+/- %.4f)", cv_scores.mean(), cv_scores.std())

    # Evaluate on train_val
    train_val_pred = clf.predict_proba(X_train)[:, 1]
    train_val_metrics = compute_all_metrics(y_train, train_val_pred, threshold=0.5)

    # Evaluate on test (report only — never used for fitting)
    test_metrics = None
    if len(test) > 0:
        X_test = test[member_cols].values
        y_test = test["label"].values
        test_pred = clf.predict_proba(X_test)[:, 1]
        test_metrics = compute_all_metrics(y_test, test_pred, threshold=0.5)
        logger.info("Test F1: %.4f, AUC: %.4f", test_metrics["f1"], test_metrics["roc_auc"])

    # Save weights
    result = {
        "method": "logistic_regression",
        "coef": clf.coef_.tolist(),
        "intercept": clf.intercept_.tolist(),
        "feature_names": member_names,
        "cv_f1_mean": float(cv_scores.mean()),
        "cv_f1_std": float(cv_scores.std()),
        "train_val_metrics": train_val_metrics,
        "test_metrics": test_metrics,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    logger.info("Saved ensemble weights to %s", output_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fit ensemble meta-classifier")
    parser.add_argument("--config", default="ml/configs/config.yaml")
    parser.add_argument("--predictions-csv", required=True, help="CSV with per-member predictions")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    config = load_config(args.config)
    output_path = resolve_path(config, config["paths"].get("ensemble_weights", "ml/evaluation/ensemble_weights.json"))
    fit_logistic_regression(Path(args.predictions_csv), output_path)


if __name__ == "__main__":
    main()
