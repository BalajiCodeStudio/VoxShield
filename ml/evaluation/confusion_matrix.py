"""Confusion matrix generation — CSV and matplotlib plot."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("voxshield.evaluation.confusion_matrix")


def generate_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_dir: str | Path | None = None,
    prefix: str = "",
) -> dict[str, Any]:
    """Generate and optionally save a confusion matrix.

    Returns the matrix as a dict for programmatic use.
    """
    from sklearn.metrics import confusion_matrix as sklearn_cm

    labels = [0, 1]
    label_names = ["REAL", "AI_GENERATED"]
    cm = sklearn_cm(y_true, y_pred, labels=labels)

    result = {
        "confusion_matrix": cm.tolist(),
        "labels": label_names,
        "true_real_pred_real": int(cm[0, 0]),
        "true_real_pred_fake": int(cm[0, 1]),
        "true_fake_pred_real": int(cm[1, 0]),
        "true_fake_pred_fake": int(cm[1, 1]),
    }

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Save CSV
        csv_path = out / f"{prefix}confusion_matrix.csv"
        with open(csv_path, "w") as f:
            f.write(f",Predicted REAL,Predicted AI_GENERATED\n")
            f.write(f"True REAL,{cm[0, 0]},{cm[0, 1]}\n")
            f.write(f"True AI_GENERATED,{cm[1, 0]},{cm[1, 1]}\n")
        logger.info("Saved confusion matrix CSV to %s", csv_path)

        # Save plot
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import seaborn as sns

            fig, ax = plt.subplots(figsize=(6, 5))
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                        xticklabels=label_names, yticklabels=label_names, ax=ax)
            ax.set_xlabel("Predicted Label")
            ax.set_ylabel("True Label")
            ax.set_title("Confusion Matrix")
            plot_path = out / f"{prefix}confusion_matrix.png"
            fig.savefig(plot_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            logger.info("Saved confusion matrix plot to %s", plot_path)
        except Exception as e:
            logger.warning("Could not save confusion matrix plot: %s", e)

    return result
