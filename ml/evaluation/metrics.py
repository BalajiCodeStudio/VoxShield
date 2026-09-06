"""Evaluation metrics for binary deepfake voice detection.

Computes: Accuracy, Precision, Recall, F1, ROC-AUC, EER, FPR, FNR.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
)


def compute_eer(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    """Compute Equal Error Rate and the corresponding threshold.

    EER is the rate where FPR == FNR.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    fnr = 1 - tpr
    # Find where |FPR - FNR| is minimized
    idx = np.nanargmin(np.abs(fpr - fnr))
    eer = float((fpr[idx] + fnr[idx]) / 2)
    threshold = float(thresholds[idx])
    return eer, threshold


def compute_all_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Compute all evaluation metrics.

    Args:
        y_true: binary labels (0=REAL, 1=AI_GENERATED)
        y_score: predicted probability of AI_GENERATED (P_fake)
        threshold: classification threshold

    Returns:
        Dictionary of all metrics.
    """
    y_pred = (y_score >= threshold).astype(int)

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    try:
        auc = roc_auc_score(y_true, y_score)
    except ValueError:
        auc = 0.0

    eer, eer_threshold = compute_eer(y_true, y_score)

    # FPR and FNR
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    fpr = fp / max(fp + tn, 1)
    fnr = fn / max(fn + tp, 1)

    return {
        "accuracy": round(float(acc), 6),
        "precision": round(float(prec), 6),
        "recall": round(float(rec), 6),
        "f1": round(float(f1), 6),
        "roc_auc": round(float(auc), 6),
        "eer": round(float(eer), 6),
        "eer_threshold": round(float(eer_threshold), 6),
        "false_positive_rate": round(float(fpr), 6),
        "false_negative_rate": round(float(fnr), 6),
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "total_samples": len(y_true),
        "threshold_used": threshold,
    }


def get_roc_curve_data(y_true: np.ndarray, y_score: np.ndarray) -> dict[str, Any]:
    """Get ROC curve data for plotting."""
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    return {
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "thresholds": thresholds.tolist(),
    }


def get_pr_curve_data(y_true: np.ndarray, y_score: np.ndarray) -> dict[str, Any]:
    """Get Precision-Recall curve data for plotting."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    return {
        "precision": precision.tolist(),
        "recall": recall.tolist(),
        "thresholds": thresholds.tolist(),
    }
