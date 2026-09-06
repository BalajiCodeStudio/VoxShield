"""
Feature extraction and audio analysis helpers for VoxShield speech anti-spoofing.
"""

from __future__ import annotations

import numpy as np
import librosa


def compute_spectral_flatness(waveform: np.ndarray) -> float:
    """Computes mean spectral flatness of audio waveform."""
    if len(waveform) < 512:
        return 0.0
    flatness = librosa.feature.spectral_flatness(y=waveform)
    return float(np.mean(flatness))


def compute_snr_db(waveform: np.ndarray) -> float:
    """Estimates simple Signal-to-Noise Ratio (SNR) in dB."""
    if len(waveform) == 0:
        return 0.0
    signal_power = np.mean(waveform ** 2)
    noise_est = np.percentile(np.abs(waveform), 10) ** 2
    if noise_est < 1e-9:
        return 40.0
    snr = 10 * np.log10(max(signal_power / noise_est, 1.0))
    return float(min(snr, 60.0))
