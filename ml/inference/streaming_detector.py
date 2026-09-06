"""
Streaming Voice Detector for VoxShield Member 1.
Maintains a sliding audio buffer for live call audio streams,
processes fixed-size windows with configurable hop size, and continuously updates risk scores.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

import numpy as np

from .detector import VoiceDetector, get_voice_detector

logger = logging.getLogger(__name__)


class StreamingVoiceDetector:
    """
    Manages continuous live audio streaming session for VoxShield.
    Buffers incoming raw PCM audio, extracts windows, runs RawTFNet inference,
    and applies temporal smoothing.
    """

    def __init__(self, detector: Optional[VoiceDetector] = None):
        self.detector = detector or get_voice_detector()
        self.sample_rate = self.detector.sample_rate
        self.window_samples = self.detector.window_samples
        self.hop_samples = self.detector.hop_samples

        self._buffer = np.array([], dtype=np.float32)
        self._total_samples_received = 0
        self._windows_processed = 0
        self._latest_result: Optional[Dict[str, Any]] = None

    def reset(self) -> None:
        """Resets streaming buffer and smoother for a new call."""
        self._buffer = np.array([], dtype=np.float32)
        self._total_samples_received = 0
        self._windows_processed = 0
        self._latest_result = None
        self.detector.smoother.reset()

    def feed_audio(self, audio_chunk: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Feeds a chunk of audio (1D float32 at sample_rate) into the buffer.
        If sufficient audio accumulates for a window, executes inference and returns updated status.
        
        Returns None if buffer is still filling.
        """
        if audio_chunk.ndim > 1:
            audio_chunk = np.mean(audio_chunk, axis=0)
        audio_chunk = audio_chunk.astype(np.float32)

        self._buffer = np.concatenate([self._buffer, audio_chunk])
        self._total_samples_received += len(audio_chunk)

        # Check if we have at least one window
        if len(self._buffer) >= self.window_samples:
            window = self._buffer[:self.window_samples]
            # Advance buffer by hop_samples
            self._buffer = self._buffer[self.hop_samples:]

            # Run inference on the window
            seg_res = self.detector.predict_segment(window)
            raw_fake = seg_res["fake_probability"]
            smoothed_fake = self.detector.smoother.update(raw_fake)
            self._windows_processed += 1

            classification = self.detector.classify(smoothed_fake, is_valid_speech=True)

            self._latest_result = {
                "prediction": classification["prediction"],
                "deepfake_score": round(smoothed_fake, 4),
                "real_probability": round(1.0 - smoothed_fake, 4),
                "fake_probability": round(smoothed_fake, 4),
                "windows_processed": self._windows_processed,
                "total_duration_sec": round(self._total_samples_received / self.sample_rate, 2),
                "model_name": self.detector.model_name,
                "model_version": "1.0.0",
                "embedding_drift_score": None,
                "reason": classification["reason"],
            }
            return self._latest_result

        return self._latest_result

    def get_latest_status(self) -> Dict[str, Any]:
        """Returns the most recent detection result or initial UNCERTAIN state."""
        if self._latest_result is not None:
            return self._latest_result
        return {
            "prediction": "UNCERTAIN",
            "deepfake_score": None,
            "real_probability": None,
            "fake_probability": None,
            "windows_processed": self._windows_processed,
            "total_duration_sec": round(self._total_samples_received / self.sample_rate, 2),
            "model_name": self.detector.model_name,
            "model_version": "1.0.0",
            "reason": "Buffering initial audio stream",
            "embedding_drift_score": None,
        }
