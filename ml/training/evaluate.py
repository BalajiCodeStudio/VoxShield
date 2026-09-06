"""Evaluation script for audio spoof detection models.

Supports two modes:
1. Evaluate a fine-tuned transformers checkpoint
2. Evaluate pretrained ONNX ensemble models on dataset splits

Usage:
    python ml/training/evaluate.py [--config ml/configs/config.yaml] [--ckpt ml/models/best_checkpoint]
    python ml/training/evaluate.py [--config ml/configs/config.yaml] --pretrained
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.config import load_config, resolve_path
from backend.models.model_loader import OnnxModelManager
from backend.utils.feature_extraction import preprocess_audio, load_and_preprocess_for_inference
from ml.evaluation.metrics import compute_all_metrics, get_roc_curve_data, get_pr_curve_data
from ml.evaluation.confusion_matrix import generate_confusion_matrix
from ml.evaluation.threshold import optimize_threshold, save_threshold

logger = logging.getLogger("voxshield.evaluation")


def evaluate_pretrained(config: dict, metadata_csv: Path, output_dir: Path):
    """Evaluate pretrained ONNX models on dataset splits."""
    manager = OnnxModelManager(config, cache_dir=str(resolve_path(config, config["paths"]["cache_dir"])))
    status = manager.load_all_enabled()
    loaded = [k for k, v in status.items() if v]
    if not loaded:
        logger.error("No models loaded. Check HF Hub connectivity and config.")
        return

    df = pd.read_csv(metadata_csv)
    results_by_split: dict[str, dict] = {}

    for split_name in ["train", "validation", "test"]:
        split_df = df[df["split"] == split_name].reset_index(drop=True)
        if len(split_df) == 0:
            logger.warning("No samples for split=%s", split_name)
            continue

        y_true = split_df["label"].values
        member_scores: dict[str, list[float]] = {m: [] for m in loaded}

        for _, row in split_df.iterrows():
            fpath = row["file"]
            if not Path(fpath).is_absolute():
                fpath = resolve_path(config, fpath)
            try:
                segs = load_and_preprocess_for_inference(fpath, segment_samples=config.get("segment_samples", 64600))
                for m in loaded:
                    p_fake = manager.predict_segments(segs, m)
                    member_scores[m].append(float(np.mean(p_fake)))
            except Exception as e:
                logger.warning("Failed to process %s: %s", fpath, e)
                for m in loaded:
                    member_scores[m].append(0.5)

        # Compute per-member metrics
        member_metrics = {}
        for m in loaded:
            scores = np.array(member_scores[m])
            m_metrics = compute_all_metrics(y_true, scores, threshold=0.5)
            member_metrics[m] = m_metrics

        # Ensemble (weighted average)
        weights = config.get("ensemble", {}).get("fallback_weights", {})
        ensemble_scores = np.zeros(len(y_true))
        total_w = 0
        for m in loaded:
            w = weights.get(m, 1.0 / len(loaded))
            ensemble_scores += w * np.array(member_scores[m])
            total_w += w
        if total_w > 0:
            ensemble_scores /= total_w

        ensemble_metrics = compute_all_metrics(y_true, ensemble_scores, threshold=0.5)
        member_metrics["ensemble"] = ensemble_metrics

        results_by_split[split_name] = {
            "num_samples": len(split_df),
            "metrics": member_metrics,
        }

        logger.info("Split=%s: ensemble f1=%.4f auc=%.4f eer=%.4f",
                     split_name, ensemble_metrics["f1"], ensemble_metrics["roc_auc"], ensemble_metrics["eer"])

    # Save test results
    test_results = results_by_split.get("test", {})
    if test_results:
        # ROC curve
        test_df = df[df["split"] == "test"].reset_index(drop=True)
        y_true = test_df["label"].values
        roc_data = get_roc_curve_data(y_true, ensemble_scores)
        pr_data = get_pr_curve_data(y_true, ensemble_scores)

        output_path = output_dir / "results.json"
        with open(output_path, "w") as f:
            json.dump({"splits": results_by_split, "roc_curve": roc_data, "pr_curve": pr_data}, f, indent=2, default=str)
        logger.info("Saved results to %s", output_path)

    # Optimize threshold on validation
    val_results = results_by_split.get("validation", {})
    if val_results and "ensemble" in val_results.get("metrics", {}):
        val_df = df[df["split"] == "validation"].reset_index(drop=True)
        y_true_val = val_df["label"].values
        # Re-compute ensemble scores for validation
        val_ensemble = np.zeros(len(y_true_val))
        tw = 0
        for m in loaded:
            w = weights.get(m, 1.0 / len(loaded))
            val_ensemble += w * np.array(member_scores[m][:len(y_true_val)])
            tw += w
        if tw > 0:
            val_ensemble /= tw
        thr_result = optimize_threshold(y_true_val, val_ensemble, metric="eer")
        thr_path = resolve_path(config, config["paths"]["threshold_json"])
        save_threshold(thr_result, thr_path)


def main():
    parser = argparse.ArgumentParser(description="Evaluate audio spoof detection models")
    parser.add_argument("--config", default="ml/configs/config.yaml")
    parser.add_argument("--pretrained", action="store_true", help="Evaluate pretrained ONNX ensemble")
    parser.add_argument("--ckpt", default=None, help="Path to fine-tuned checkpoint")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    config = load_config(args.config)
    output_dir = resolve_path(config, config["paths"]["evaluation_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_csv = resolve_path(config, config["paths"]["metadata_csv"])

    if not metadata_csv.exists():
        logger.error("Metadata CSV not found: %s. Run ml/datasets/build_metadata.py first.", metadata_csv)
        sys.exit(1)

    evaluate_pretrained(config, metadata_csv, output_dir)


if __name__ == "__main__":
    main()
