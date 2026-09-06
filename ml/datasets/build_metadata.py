"""Build metadata.csv and speaker-disjoint splits from audio files.

Reads audio from ml/datasets/real/ and ml/datasets/synthetic/.
Optionally uses ASVspoof protocol files for speaker/generator info.

Usage:
    python ml/datasets/build_metadata.py [--config ml/configs/config.yaml]
    python ml/datasets/build_metadata.py --asvspoof-protocol /path/to/protocol.txt
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.config import load_config, resolve_path

logger = logging.getLogger("voxshield.datasets")
SEED = 42
SUPPORTED_EXT = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}


def scan_audio_dir(audio_dir: Path) -> list[dict]:
    """Scan a directory for audio files, returning file metadata."""
    files = []
    for ext in SUPPORTED_EXT:
        for f in sorted(audio_dir.rglob(f"*{ext}")):
            files.append({
                "file": str(f),
                "label": 1 if "synthetic" in str(audio_dir).lower() or "fake" in str(audio_dir).lower() else 0,
                "speaker_id": "unknown",
                "dataset": audio_dir.parent.name,
                "generator": "unknown",
            })
    return files


def speaker_disjoint_split(
    df: pd.DataFrame,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = SEED,
) -> pd.DataFrame:
    """Split by speaker_id to prevent data leakage.

    Speakers in train, validation, and test are completely disjoint.
    If speaker_id is 'unknown', falls back to file-level split.
    """
    rng = np.random.RandomState(seed)

    known_speakers = df[df["speaker_id"] != "unknown"]["speaker_id"].unique()
    unknown_mask = df["speaker_id"] == "unknown"

    if len(known_speakers) > 0:
        rng.shuffle(known_speakers)
        n_test = max(1, int(len(known_speakers) * test_ratio))
        n_val = max(1, int(len(known_speakers) * val_ratio))
        test_speakers = set(known_speakers[:n_test])
        val_speakers = set(known_speakers[n_test:n_test + n_val])
        train_speakers = set(known_speakers[n_test + n_val:])

        conditions = []
        for _, row in df.iterrows():
            if row["speaker_id"] in test_speakers:
                conditions.append("test")
            elif row["speaker_id"] in val_speakers:
                conditions.append("validation")
            elif row["speaker_id"] in train_speakers:
                conditions.append("train")
            else:
                conditions.append("unknown")
        df = df.copy()
        df["split"] = conditions
    else:
        # Fallback: random file-level split
        indices = np.arange(len(df))
        rng.shuffle(indices)
        n_test = max(1, int(len(df) * test_ratio))
        n_val = max(1, int(len(df) * val_ratio))
        splits = ["train"] * len(df)
        for i in indices[:n_test]:
            splits[i] = "test"
        for i in indices[n_test:n_test + n_val]:
            splits[i] = "validation"
        df = df.copy()
        df["split"] = splits

    return df


def main():
    parser = argparse.ArgumentParser(description="Build metadata and splits")
    parser.add_argument("--config", default="ml/configs/config.yaml")
    parser.add_argument("--asvspoof-protocol", default=None, help="ASVspoof protocol file path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    config = load_config(args.config)
    datasets_dir = resolve_path(config, config["paths"]["datasets_dir"])
    real_dir = datasets_dir / "real"
    synthetic_dir = datasets_dir / "synthetic"

    all_files = []
    if real_dir.exists():
        all_files.extend(scan_audio_dir(real_dir))
    if synthetic_dir.exists():
        all_files.extend(scan_audio_dir(synthetic_dir))

    if not all_files:
        logger.error("No audio files found in %s or %s", real_dir, synthetic_dir)
        sys.exit(1)

    df = pd.DataFrame(all_files)
    logger.info("Found %d audio files (%d real, %d synthetic)",
                len(df), (df["label"] == 0).sum(), (df["label"] == 1).sum())

    # Split
    df = speaker_disjoint_split(df, seed=config.get("seed", SEED))

    # Save metadata
    metadata_path = resolve_path(config, config["paths"]["metadata_csv"])
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(metadata_path, index=False)
    logger.info("Saved metadata to %s", metadata_path)

    # Save splits
    splits_dir = resolve_path(config, config["paths"]["splits_dir"])
    splits_dir.mkdir(parents=True, exist_ok=True)
    for split_name in ["train", "validation", "test"]:
        split_df = df[df["split"] == split_name].reset_index(drop=True)
        split_path = splits_dir / f"{split_name}.csv"
        split_df.to_csv(split_path, index=False)
        logger.info("  %s: %d samples", split_name, len(split_df))


if __name__ == "__main__":
    main()
