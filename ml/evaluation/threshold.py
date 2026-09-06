"""
Threshold selection module for VoxShield Voice Deepfake Detector.
Finds the optimal classification threshold (EER threshold or F1-maximization)
using STRICTLY the validation set.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, List, Union
from .metrics import compute_eer


def select_eer_threshold(
    val_y_true: Union[List[int], np.ndarray],
    val_y_scores: Union[List[float], np.ndarray],
) -> Tuple[float, float]:
    """
    Computes optimal EER threshold using ONLY validation data.
    
    Returns:
        (optimal_threshold, validation_eer)
    """
    val_y_true_arr = np.array(val_y_true, dtype=int)
    val_y_scores_arr = np.array(val_y_scores, dtype=float)

    val_eer, opt_thresh = compute_eer(val_y_true_arr, val_y_scores_arr)
    return float(opt_thresh), float(val_eer)


def select_best_f1_threshold(
    val_y_true: Union[List[int], np.ndarray],
    val_y_scores: Union[List[float], np.ndarray],
    threshold_steps: int = 100,
) -> Tuple[float, float]:
    """
    Finds threshold that maximizes F1 score on validation set.
    """
    val_y_true_arr = np.array(val_y_true, dtype=int)
    val_y_scores_arr = np.array(val_y_scores, dtype=float)

    best_thresh = 0.50
    best_f1 = 0.0

    from sklearn.metrics import f1_score

    for t in np.linspace(0.05, 0.95, threshold_steps):
        preds = (val_y_scores_arr >= t).astype(int)
        score = f1_score(val_y_true_arr, preds, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_thresh = float(t)

    return float(best_thresh), float(best_f1 * 100.0)
