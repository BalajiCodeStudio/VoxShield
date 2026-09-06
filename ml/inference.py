"""CLI inference script for VoxShield deepfake voice detection.

Usage:
    python ml/inference.py --audio sample.wav
    python ml/inference.py --audio sample.wav --config ml/configs/config.yaml
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "ml"))

from ml.inference.detector import VoiceDetector


def main():
    parser = argparse.ArgumentParser(description="VoxShield Voice Deepfake Detection")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--config", default=None, help="Config file path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    detector = VoiceDetector(config=args.config)
    detector.load_model()

    result = detector.predict(args.audio)

    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))

    sys.exit(0 if result.get("prediction") != "UNCERTAIN" or result.get("deepfake_score") is not None else 1)


if __name__ == "__main__":
    main()
