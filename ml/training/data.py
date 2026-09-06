"""Audio Dataset for training wav2vec2-based classifiers with augmentation."""
from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

logger = logging.getLogger("voxshield.training.data")

SEED = 42
TARGET_SR = 16000


class AudioDataset(Dataset):
    """PyTorch dataset for audio spoof detection.

    Reads metadata CSV (file, label, speaker_id, dataset, generator, split).
    Loads audio on the fly with optional augmentation for training splits.
    """

    def __init__(
        self,
        metadata_csv: str | Path,
        split: str = "train",
        processor: Any = None,
        max_length: int = 16000 * 10,
        augment: bool = False,
        augment_cfg: dict | None = None,
    ):
        self.df = pd.read_csv(metadata_csv)
        self.df = self.df[self.df["split"] == split].reset_index(drop=True)
        self.processor = processor
        self.max_length = max_length
        self.augment = augment and split == "train"
        self.augment_cfg = augment_cfg or {}

        if len(self.df) == 0:
            logger.warning("No samples found for split=%s in %s", split, metadata_csv)
        else:
            logger.info("Loaded %d samples for split=%s", len(self.df), split)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.df.iloc[idx]
        audio_path = str(row["file"])
        label = int(row["label"])

        # Load audio
        waveform = self._load_audio(audio_path)

        # Augment if training
        if self.augment:
            waveform = self._augment(waveform)

        # Truncate or pad
        if len(waveform) > self.max_length:
            waveform = waveform[:self.max_length]
        else:
            waveform = np.pad(waveform, (0, max(0, self.max_length - len(waveform))))

        # Processor
        if self.processor is not None:
            inputs = self.processor(waveform, sampling_rate=TARGET_SR, return_tensors="pt", padding=True)
            return {
                "input_values": inputs["input_values"].squeeze(0),
                "attention_mask": inputs.get("attention_mask", torch.ones_like(inputs["input_values"])).squeeze(0),
                "labels": torch.tensor(label, dtype=torch.long),
            }

        return {
            "waveform": torch.tensor(waveform, dtype=torch.float32),
            "labels": torch.tensor(label, dtype=torch.long),
        }

    def _load_audio(self, path: str) -> np.ndarray:
        """Load and preprocess audio to 16kHz mono float32."""
        try:
            import soundfile as sf
            data, sr = sf.read(path, dtype="float32", always_2d=True)
        except Exception:
            # Fallback to librosa
            import librosa
            data, sr = librosa.load(path, sr=TARGET_SR, mono=True)
            if data.ndim == 1:
                return data.astype(np.float32)
            return data.mean(axis=1).astype(np.float32)

        if data.ndim > 1:
            data = data.mean(axis=1)

        # Resample if needed
        if sr != TARGET_SR:
            import librosa
            data = librosa.resample(data, orig_sr=sr, target_sr=TARGET_SR)

        return data.astype(np.float32)

    def _augment(self, waveform: np.ndarray) -> np.ndarray:
        """Apply augmentation: noise, gain, lowpass."""
        cfg = self.augment_cfg

        # Additive noise
        snr_db = cfg.get("add_noise_snr_db", 20)
        if random.random() < 0.5:
            noise = np.random.randn(len(waveform)).astype(np.float32)
            signal_power = np.mean(waveform ** 2)
            noise_power = np.mean(noise ** 2)
            snr_linear = 10 ** (snr_db / 10)
            noise = noise * np.sqrt(signal_power / (noise_power * snr_linear + 1e-10))
            waveform = waveform + noise

        # Volume variation
        vol_range = cfg.get("volume_range", [0.8, 1.2])
        if random.random() < 0.5:
            gain = random.uniform(vol_range[0], vol_range[1])
            waveform = waveform * gain

        # Random gain in dB
        gain_db = cfg.get("random_gain_db", 3)
        if random.random() < 0.3:
            gain = 10 ** (random.uniform(-gain_db, gain_db) / 20)
            waveform = waveform * gain

        # Lowpass filter
        if cfg.get("lowpass_cutoff_hz") and random.random() < 0.3:
            try:
                from scipy.signal import butter, sosfilt
                cutoff = cfg["lowpass_cutoff_hz"]
                sos = butter(5, cutoff, btype="low", fs=TARGET_SR, output="sos")
                waveform = sosfilt(sos, waveform).astype(np.float32)
            except Exception:
                pass

        # Clip to [-1, 1]
        waveform = np.clip(waveform, -1.0, 1.0)
        return waveform


def load_metadata_splits(
    metadata_csv: str | Path,
    splits_dir: str | Path | None = None,
) -> dict[str, pd.DataFrame]:
    """Load train/validation/test splits from metadata or split CSV files."""
    metadata_csv = Path(metadata_csv)

    if splits_dir:
        splits_dir = Path(splits_dir)
        result = {}
        for split in ["train", "validation", "test"]:
            csv_path = splits_dir / f"{split}.csv"
            if csv_path.exists():
                result[split] = pd.read_csv(csv_path)
            elif metadata_csv.exists():
                df = pd.read_csv(metadata_csv)
                result[split] = df[df["split"] == split].reset_index(drop=True)
        return result

    if metadata_csv.exists():
        df = pd.read_csv(metadata_csv)
        return {
            "train": df[df["split"] == "train"].reset_index(drop=True),
            "validation": df[df["split"] == "validation"].reset_index(drop=True),
            "test": df[df["split"] == "test"].reset_index(drop=True),
        }

    raise FileNotFoundError(f"Metadata not found: {metadata_csv}")
