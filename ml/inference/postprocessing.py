"""
Postprocessing and Temporal Smoothing module for VoxShield Voice Deepfake Detector.
Implements Exponential Moving Average (EMA), sliding window averaging, hysteresis,
and decision boundary calibration.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
import numpy as np


class TemporalSmoother:
    """
    Applies temporal smoothing across sequential inference window predictions.
    Supports Exponential Moving Average (EMA) and Moving Average (MA) with hysteresis.
    """

    def __init__(
        self,
        method: str = "ema",
        alpha: float = 0.4,
        window_size: int = 5,
        threshold_low: float = 0.45,
        threshold_high: float = 0.55,
    ):
        self.method = method.lower()
        self.alpha = float(alpha)
        self.window_size = int(window_size)
        self.threshold_low = float(threshold_low)
        self.threshold_high = float(threshold_high)

        self._history: List[float] = []
        self._current_ema: Optional[float] = None
        self._last_state: str = "UNCERTAIN"

    def reset(self) -> None:
        """Resets smoother state for a new call session."""
        self._history.clear()
        self._current_ema = None
        self._last_state = "UNCERTAIN"

    def update(self, raw_fake_prob: float) -> float:
        """
        Updates the smoother with a new window prediction.
        Returns the smoothed fake probability.
        """
        raw_fake_prob = float(np.clip(raw_fake_prob, 0.0, 1.0))
        self._history.append(raw_fake_prob)

        if self.method == "ema":
            if self._current_ema is None:
                self._current_ema = raw_fake_prob
            else:
                self._current_ema = self.alpha * raw_fake_prob + (1.0 - self.alpha) * self._current_ema
            smoothed = self._current_ema
        else:
            # Moving Average
            recent = self._history[-self.window_size:]
            smoothed = float(np.mean(recent))

        return float(np.clip(smoothed, 0.0, 1.0))

    def classify_with_hysteresis(
        self,
        smoothed_fake_prob: float,
        uncertain_margin: float = 0.05,
    ) -> str:
        """
        Classifies prediction using dual thresholds to prevent rapid oscillation:
        - REAL if smoothed_fake_prob < threshold_low - uncertain_margin
        - AI_GENERATED if smoothed_fake_prob > threshold_high + uncertain_margin
        - UNCERTAIN if near decision boundary [0.45, 0.55]
        """
        if smoothed_fake_prob > self.threshold_high + uncertain_margin:
            self._last_state = "AI_GENERATED"
        elif smoothed_fake_prob < self.threshold_low - uncertain_margin:
            self._last_state = "REAL"
        else:
            # In the hysteresis / uncertain band
            if self._last_state == "UNCERTAIN":
                self._last_state = "UNCERTAIN"
            # If previously certain, remain in previous state unless it crosses boundary
        return self._last_state


def aggregate_segment_scores(
    scores: List[float],
    method: str = "mean",
    trim_percent: float = 0.1,
) -> float:
    """
    Aggregates scores across multiple speech segments.
    Methods: 'mean', 'median', 'trimmed_mean', 'max'.
    """
    if not scores:
        return 0.5

    arr = np.array(scores, dtype=np.float32)
    if method == "median":
        return float(np.median(arr))
    elif method == "max":
        return float(np.max(arr))
    elif method == "trimmed_mean" and len(arr) >= 4:
        lower = np.percentile(arr, trim_percent * 100)
        upper = np.percentile(arr, (1.0 - trim_percent) * 100)
        trimmed = arr[(arr >= lower) & (arr <= upper)]
        return float(np.mean(trimmed)) if len(trimmed) > 0 else float(np.mean(arr))
    else:
        return float(np.mean(arr))
