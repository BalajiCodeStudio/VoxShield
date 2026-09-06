"""Export a fine-tuned PyTorch classifier to ONNX format.

Performs automated verification: compares PyTorch vs ONNX predictions.
Fails if divergence exceeds configurable tolerance.

Usage:
    python ml/training/export_onnx.py --ckpt ml/models/best_checkpoint --output ml/models/voice_detector.onnx
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.config import load_config, resolve_path

logger = logging.getLogger("voxshield.training.export_onnx")

TOLERANCE = 1e-4  # Max absolute difference between PyTorch and ONNX outputs


def export_to_onnx(checkpoint_dir: str | Path, output_path: str | Path, opset: int = 17):
    """Export a Wav2Vec2ForSequenceClassification to ONNX."""
    from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor

    checkpoint_dir = Path(checkpoint_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading model from %s", checkpoint_dir)
    model = Wav2Vec2ForSequenceClassification.from_pretrained(str(checkpoint_dir))
    processor = Wav2Vec2FeatureExtractor.from_pretrained(str(checkpoint_dir))
    model.eval()

    # Create dummy input
    dummy_input = torch.randn(1, 64600, dtype=torch.float32)

    logger.info("Exporting to ONNX (opset=%d)", opset)
    torch.onnx.export(
        model,
        (dummy_input,),
        str(output_path),
        opset_version=opset,
        input_names=["input_values"],
        output_names=["logits"],
        dynamic_axes={
            "input_values": {0: "batch", 1: "sequence"},
            "logits": {0: "batch"},
        },
    )
    logger.info("Exported ONNX model to %s", output_path)
    return output_path


def verify_parity(checkpoint_dir: str | Path, onnx_path: str | Path, num_samples: int = 10):
    """Compare PyTorch vs ONNX Runtime predictions."""
    import onnxruntime as ort
    from transformers import Wav2Vec2ForSequenceClassification

    checkpoint_dir = Path(checkpoint_dir)
    onnx_path = Path(onnx_path)

    model = Wav2Vec2ForSequenceClassification.from_pretrained(str(checkpoint_dir))
    model.eval()

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

    max_abs_diffs = []
    rel_diffs = []

    for i in range(num_samples):
        dummy = torch.randn(1, 64600)
        with torch.no_grad():
            torch_out = torch.softmax(model(dummy).logits, dim=-1).numpy()

        onnx_out = session.run(None, {"input_values": dummy.numpy()})[0]
        onnx_probs = np.exp(onnx_out) / np.exp(onnx_out).sum(axis=-1, keepdims=True)

        max_diff = float(np.max(np.abs(torch_out - onnx_out)))
        rel = float(np.max(np.abs(torch_out - onnx_out) / (np.abs(torch_out) + 1e-10)))
        max_abs_diffs.append(max_diff)
        rel_diffs.append(rel)

    result = {
        "num_samples": num_samples,
        "max_abs_difference": max(max_abs_diffs),
        "mean_abs_difference": np.mean(max_abs_diffs),
        "max_rel_difference": max(rel_diffs),
        "mean_rel_difference": float(np.mean(rel_diffs)),
        "tolerance": TOLERANCE,
        "passed": max(max_abs_diffs) <= TOLERANCE,
    }

    logger.info("Parity check: max_diff=%.6f, passed=%s", result["max_abs_difference"], result["passed"])
    return result


def main():
    parser = argparse.ArgumentParser(description="Export model to ONNX")
    parser.add_argument("--ckpt", required=True, help="Path to fine-tuned checkpoint")
    parser.add_argument("--output", default="ml/models/voice_detector.onnx", help="Output ONNX path")
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    output_path = Path(args.output) if Path(args.output).is_absolute() else PROJECT_ROOT / args.output

    if not args.verify_only:
        export_to_onnx(args.ckpt, output_path, opset=args.opset)

    result = verify_parity(args.ckpt, output_path)

    # Save verification result
    ver_path = output_path.parent / f"{output_path.stem}.verification.json"
    with open(ver_path, "w") as f:
        json.dump(result, f, indent=2)

    if not result["passed"]:
        logger.error("ONNX export verification FAILED. Max diff: %.6f > tolerance %.6f",
                      result["max_abs_difference"], TOLERANCE)
        sys.exit(1)
    else:
        logger.info("ONNX export verification PASSED")


if __name__ == "__main__":
    main()
