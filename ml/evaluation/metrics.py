"""
Evaluation metrics module for VoxShield Voice Deepfake Detector.
Computes Accuracy, Precision, Recall, F1, ROC-AUC, EER, FPR, FNR, and Confusion Matrix.
Strict scientific integrity: All metrics computed from real model output predictions.
"""

from __future__ import annotations

from typing import Dict, Any, List, Union, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
)
from scipy.optimize import brentq
from scipy.interpolate import interp1d


def compute_eer(y_true: np.ndarray, y_scores: np.ndarray) -> Tuple[float, float]:
    """
    Computes Equal Error Rate (EER) and the corresponding optimal threshold.
    y_true: 0 for REAL (bonafide), 1 for AI_GENERATED (spoof).
    y_scores: predicted probability/score for AI_GENERATED (higher = more fake).
    
    Returns:
        (eer_percentage, eer_threshold)
    """
    y_true = np.asarray(y_true, dtype=int)
    y_scores = np.asarray(y_scores, dtype=float)

    if len(np.unique(y_true)) < 2:
        return 50.0, 0.50

    fpr, tpr, thresholds = roc_curve(y_true, y_scores, pos_label=1)
    fnr = 1.0 - tpr

    # Find the threshold index where FPR is closest to FNR
    diffs = np.abs(fpr - fnr)
    min_idx = int(np.argmin(diffs))
    eer = float((fpr[min_idx] + fnr[min_idx]) / 2.0 * 100.0)
    opt_thresh = float(thresholds[min_idx])
    if np.isnan(opt_thresh) or np.isinf(opt_thresh) or opt_thresh > 1.0 or opt_thresh < 0.0:
        opt_thresh = 0.50
    return eer, opt_thresh


def calculate_metrics(
    y_true: Union[List[int], np.ndarray],
    y_pred_probs: Union[List[float], np.ndarray],
    threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Computes comprehensive classification metrics from ground truth and predicted probabilities.
    
    Labels:
        0 = REAL / Bonafide
        1 = AI_GENERATED / Spoof
    """
    y_true_arr = np.array(y_true, dtype=int)
    y_probs_arr = np.array(y_pred_probs, dtype=float)

    # Hard predictions based on threshold
    y_pred = (y_probs_arr >= threshold).astype(int)

    # Confusion matrix
    cm = confusion_matrix(y_true_arr, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Derived rates
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    acc = float(accuracy_score(y_true_arr, y_pred) * 100.0)
    prec = float(precision_score(y_true_arr, y_pred, zero_division=0) * 100.0)
    rec = float(recall_score(y_true_arr, y_pred, zero_division=0) * 100.0)
    f1 = float(f1_score(y_true_arr, y_pred, zero_division=0) * 100.0)

    try:
        roc_auc = float(roc_auc_score(y_true_arr, y_probs_arr) * 100.0)
    except Exception:
        roc_auc = 0.0

    eer_val, eer_thresh = compute_eer(y_true_arr, y_probs_arr)

    return {
        "accuracy_percent": round(acc, 2),
        "precision_percent": round(prec, 2),
        "recall_percent": round(rec, 2),
        "f1_percent": round(f1, 2),
        "roc_auc_percent": round(roc_auc, 2),
        "eer_percent": round(eer_val, 2),
        "eer_threshold": round(eer_thresh, 4),
        "evaluation_threshold": round(threshold, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": {
            "true_negatives_real_as_real": int(tn),
            "false_positives_real_as_fake": int(fp),
            "false_negatives_fake_as_real": int(fn),
            "true_positives_fake_as_fake": int(tp),
        },
        "total_samples": len(y_true_arr),
        "total_real": int(np.sum(y_true_arr == 0)),
        "total_fake": int(np.sum(y_true_arr == 1)),
    }
