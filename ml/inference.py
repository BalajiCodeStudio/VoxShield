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

from backend.utils.config import load_config
from backend.services.voice_detector import VoiceDetector


def main():
    parser = argparse.ArgumentParser(description="VoxShield Voice Deepfake Detection")
    parser.add_argument("--audio", required=True, help="Path to audio file")
    parser.add_argument("--config", default=None, help="Config file path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    config = load_config(args.config) if args.config else load_config()
    detector = VoiceDetector(config)
    detector.load_models()

    result = detector.predict_file(args.audio)

    if args.pretty:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(json.dumps(result.to_dict()))

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
