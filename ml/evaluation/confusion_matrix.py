"""
Confusion Matrix visualizer and formatter for VoxShield evaluation.
"""

from __future__ import annotations

from typing import Dict, Any, List, Union
import numpy as np


def format_confusion_matrix(cm_dict: Dict[str, int]) -> str:
    """Formats confusion matrix dictionary into a clean markdown table."""
    tn = cm_dict.get("true_negatives_real_as_real", 0)
    fp = cm_dict.get("false_positives_real_as_fake", 0)
    fn = cm_dict.get("false_negatives_fake_as_real", 0)
    tp = cm_dict.get("true_positives_fake_as_fake", 0)

    table = (
        "| Actual \\ Predicted | Predicted REAL (0) | Predicted AI_GENERATED (1) | Total |\n"
        "| :--- | :---: | :---: | :---: |\n"
        f"| **Actual REAL (0)** | {tn} (TN) | {fp} (FP) | {tn + fp} |\n"
        f"| **Actual AI_GENERATED (1)** | {fn} (FN) | {tp} (TP) | {fn + tp} |\n"
        f"| **Total** | {tn + fn} | {fp + tp} | {tn + fp + fn + tp} |"
    )
    return table
