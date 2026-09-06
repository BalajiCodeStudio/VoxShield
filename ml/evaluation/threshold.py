"""Threshold optimization from validation data.

The decision threshold is optimized on the VALIDATION set only.
The TEST set is NEVER used for threshold selection.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from ml.evaluation.metrics import compute_all_metrics

logger = logging.getLogger("voxshield.evaluation.threshold")


def optimize_threshold(
    y_true: np.ndarray,
    y_score: np.ndarray,
    metric: str = "eer",
    num_thresholds: int = 500,
) -> dict[str, Any]:
    """Find the optimal threshold on validation data.

    Args:
        y_true: binary validation labels
        y_score: P(fake) scores from model(s)
        metric: optimization target — 'eer', 'f1', or 'balanced'
        num_thresholds: number of candidate thresholds to evaluate

    Returns:
        Dictionary with optimal threshold, metric value, and per-threshold results.
    """
    thresholds = np.linspace(0.01, 0.99, num_thresholds)

    if metric == "eer":
        from ml.evaluation.metrics import compute_eer
        _, best_thr = compute_eer(y_true, y_score)
        best_metrics = compute_all_metrics(y_true, y_score, threshold=best_thr)
    elif metric == "f1":
        best_f1 = -1.0
        best_thr = 0.5
        best_metrics = {}
        for thr in thresholds:
            m = compute_all_metrics(y_true, y_score, threshold=thr)
            if m["f1"] > best_f1:
                best_f1 = m["f1"]
                best_thr = thr
                best_metrics = m
    elif metric == "balanced":
        best_score = -1.0
        best_thr = 0.5
        best_metrics = {}
        for thr in thresholds:
            m = compute_all_metrics(y_true, y_score, threshold=thr)
            # Balanced accuracy = (TPR + TNR) / 2
            tpr = m["recall"]
            tnr = 1 - m["false_positive_rate"]
            bal_acc = (tpr + tnr) / 2
            if bal_acc > best_score:
                best_score = bal_acc
                best_thr = thr
                best_metrics = m
    else:
        raise ValueError(f"Unknown metric: {metric}. Use 'eer', 'f1', or 'balanced'.")

    return {
        "fake_threshold": round(float(best_thr), 4),
        "real_threshold": round(float(best_thr), 4),
        "uncertain_band": round(float(0.0), 4),
        "optimization_metric": metric,
        "metrics_at_threshold": best_metrics,
        "num_validation_samples": len(y_true),
        "optimization_date": datetime.now(timezone.utc).isoformat(),
    }


def save_threshold(result: dict[str, Any], path: str | Path) -> None:
    """Save threshold configuration to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    logger.info("Saved threshold config to %s", path)
