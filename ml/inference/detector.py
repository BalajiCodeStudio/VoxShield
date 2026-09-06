"""
Core Voice Deepfake Detector for VoxShield Member 1.
Orchestrates audio preprocessing, Silero VAD, RawTFNet inference, and postprocessing.
Loads model ONLY ONCE into memory.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

import numpy as np
import yaml

from .models.rawtfnet import RawTFNetModel, pad_or_crop_waveform
from .postprocessing import TemporalSmoother, aggregate_segment_scores
from backend.utils.audio import load_and_preprocess_audio, extract_speech_segments

logger = logging.getLogger(__name__)

# Singleton cache for VoiceDetector
_GLOBAL_DETECTOR: Optional[VoiceDetector] = None


class VoiceDetector:
    """
    Main VoxShield Voice Deepfake Detector.
    Encapsulates RawTFNet inference, VAD, smoothing, and Member 1 API contract.
    """

    def __init__(self, config: Optional[Union[Dict[str, Any], str]] = None):
        if isinstance(config, str):
            with open(config, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        elif isinstance(config, dict):
            self.config = config
        else:
            self.config = self._load_default_config()

        # Extract config params
        model_cfg = self.config.get("model", {})
        audio_cfg = self.config.get("audio", {})
        inf_cfg = self.config.get("inference", {})
        smooth_cfg = self.config.get("smoothing", {})
        vad_cfg = self.config.get("vad", {})

        self.model_name = model_cfg.get("name", "RawTFNet")
        self.sample_rate = int(audio_cfg.get("sample_rate", 16000))
        self.window_seconds = float(audio_cfg.get("window_seconds", 4.0375))
        self.window_samples = int(round(self.sample_rate * self.window_seconds))
        self.hop_seconds = float(audio_cfg.get("hop_seconds", 2.0))
        self.hop_samples = int(round(self.sample_rate * self.hop_seconds))

        self.threshold = float(inf_cfg.get("threshold", 0.50))
        self.uncertain_margin = float(inf_cfg.get("uncertain_margin", 0.05))
        self.min_speech_duration = float(inf_cfg.get("min_speech_duration", 0.3))
        self.vad_enabled = bool(vad_cfg.get("enabled", True))
        self.use_onnx = bool(model_cfg.get("use_onnx", False))

        # Model instance (loads once)
        self.model = RawTFNetModel(
            use_onnx=self.use_onnx,
            device="cpu",
            sample_rate=self.sample_rate,
            window_samples=self.window_samples,
        )

        # Postprocessing smoother
        self.smoother = TemporalSmoother(
            method=smooth_cfg.get("method", "ema"),
            alpha=float(smooth_cfg.get("alpha", 0.4)),
            threshold_low=self.threshold - self.uncertain_margin,
            threshold_high=self.threshold + self.uncertain_margin,
        )

    def _load_default_config(self) -> Dict[str, Any]:
        """Loads configuration from ml/configs/config.yaml or returns defaults."""
        config_paths = [
            Path(__file__).resolve().parents[1] / "configs" / "config.yaml",
            Path("ml/configs/config.yaml"),
        ]
        for p in config_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return yaml.safe_load(f) or {}
                except Exception:
                    pass
        return {
            "model": {"name": "RawTFNet", "use_onnx": False},
            "audio": {"sample_rate": 16000, "window_seconds": 4.0375, "hop_seconds": 2.0},
            "inference": {"threshold": 0.50, "uncertain_margin": 0.05, "min_speech_duration": 0.3},
            "vad": {"enabled": True},
            "smoothing": {"method": "ema", "alpha": 0.4},
        }

    def load_model(self) -> None:
        """Loads the model into memory. Safe to call multiple times (loads once)."""
        if not self.model.is_loaded:
            self.model.load()

    def preprocess_audio(self, audio: Union[bytes, str, np.ndarray]) -> np.ndarray:
        """Preprocesses input into 16 kHz mono float32 normalized waveform."""
        return load_and_preprocess_audio(audio, target_sr=self.sample_rate, normalize=True)

    def predict_segment(self, waveform: np.ndarray) -> Dict[str, Any]:
        """
        Runs inference on a single audio segment (e.g. 64,600 samples).
        """
        self.load_model()
        fake_prob, real_prob, logits = self.model.predict(waveform)
        return {
            "fake_probability": float(fake_prob),
            "real_probability": float(real_prob),
            "logits": logits.tolist() if isinstance(logits, np.ndarray) else logits,
        }

    def predict_stream(self, waveform: np.ndarray) -> List[Dict[str, Any]]:
        """
        Performs streaming-style windowed inference across continuous audio with hop_samples.
        """
        self.load_model()
        if len(waveform) == 0:
            return []

        results = []
        if len(waveform) <= self.window_samples:
            res = self.predict_segment(waveform)
            results.append(res)
            return results

        # Sliding window over the waveform
        for start_idx in range(0, len(waveform) - self.hop_samples, self.hop_samples):
            window = waveform[start_idx : start_idx + self.window_samples]
            if len(window) < int(self.sample_rate * self.min_speech_duration):
                break
            res = self.predict_segment(window)
            results.append(res)

        return results

    def aggregate_predictions(self, segment_results: List[Dict[str, Any]]) -> float:
        """Aggregates multiple window fake probabilities into a single score."""
        if not segment_results:
            return 0.5
        scores = [r["fake_probability"] for r in segment_results]
        return aggregate_segment_scores(scores, method="mean")

    def classify(self, fake_probability: Optional[float], is_valid_speech: bool = True) -> Dict[str, Any]:
        """
        Maps probability to REAL / AI_GENERATED / UNCERTAIN class with explanation.
        """
        if not is_valid_speech or fake_probability is None:
            return {
                "prediction": "UNCERTAIN",
                "reason": "Insufficient speech or silent audio",
                "deepfake_score": None,
            }

        # Check uncertainty boundary
        lower_bound = self.threshold - self.uncertain_margin
        upper_bound = self.threshold + self.uncertain_margin

        if lower_bound <= fake_probability <= upper_bound:
            return {
                "prediction": "UNCERTAIN",
                "reason": f"Probability ({fake_probability:.3f}) is near decision boundary [{lower_bound:.2f}, {upper_bound:.2f}]",
                "deepfake_score": round(fake_probability, 4),
            }
        elif fake_probability > upper_bound:
            return {
                "prediction": "AI_GENERATED",
                "reason": "Detected synthetic / deepfake speech characteristics",
                "deepfake_score": round(fake_probability, 4),
            }
        else:
            return {
                "prediction": "REAL",
                "reason": "Speech exhibits natural human acoustic patterns",
                "deepfake_score": round(fake_probability, 4),
            }

    def predict(self, audio_input: Union[bytes, str, np.ndarray]) -> Dict[str, Any]:
        """
        Full inference pipeline:
        Audio -> Preprocessing -> VAD -> Slicing -> RawTFNet -> Smoothing -> Output Contract.
        """
        t0 = time.perf_counter()
        self.load_model()

        try:
            waveform = self.preprocess_audio(audio_input)
        except Exception as e:
            logger.warning(f"Audio preprocessing error: {e}")
            return {
                "prediction": "UNCERTAIN",
                "reason": f"Invalid or unreadable audio: {str(e)}",
                "deepfake_score": None,
                "real_probability": None,
                "fake_probability": None,
                "segments_analyzed": 0,
                "processing_time_ms": round((time.perf_counter() - t0) * 1000, 2),
                "model_name": self.model_name,
                "model_version": "1.0.0",
                "embedding_drift_score": None,
            }

        # Check minimum length
        duration_sec = len(waveform) / self.sample_rate
        if duration_sec < self.min_speech_duration or np.max(np.abs(waveform)) < 1e-4:
            return {
                "prediction": "UNCERTAIN",
                "reason": f"Audio too short ({duration_sec:.2f}s < {self.min_speech_duration}s) or silent",
                "deepfake_score": None,
                "real_probability": None,
                "fake_probability": None,
                "segments_analyzed": 0,
                "processing_time_ms": round((time.perf_counter() - t0) * 1000, 2),
                "model_name": self.model_name,
                "model_version": "1.0.0",
                "embedding_drift_score": None,
            }

        # Apply VAD if enabled
        if self.vad_enabled:
            speech_segments = extract_speech_segments(waveform, sr=self.sample_rate, min_speech_duration=self.min_speech_duration)
            if not speech_segments:
                return {
                    "prediction": "UNCERTAIN",
                    "reason": "No valid speech detected by VAD",
                    "deepfake_score": None,
                    "real_probability": None,
                    "fake_probability": None,
                    "segments_analyzed": 0,
                    "processing_time_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "model_name": self.model_name,
                    "model_version": "1.0.0",
                    "embedding_drift_score": None,
                }
            active_audio = np.concatenate(speech_segments)
        else:
            active_audio = waveform

        # Run streaming window inference
        segment_results = self.predict_stream(active_audio)
        raw_fake_prob = self.aggregate_predictions(segment_results)

        # Apply temporal smoothing
        smoothed_fake_prob = self.smoother.update(raw_fake_prob)
        smoothed_real_prob = 1.0 - smoothed_fake_prob

        # Classify
        classification = self.classify(smoothed_fake_prob, is_valid_speech=True)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "prediction": classification["prediction"],
            "deepfake_score": round(smoothed_fake_prob, 4),
            "real_probability": round(smoothed_real_prob, 4),
            "fake_probability": round(smoothed_fake_prob, 4),
            "segments_analyzed": len(segment_results),
            "processing_time_ms": elapsed_ms,
            "model_name": self.model_name,
            "model_version": "1.0.0",
            "reason": classification["reason"],
            "embedding_drift_score": None,
        }

    # Backward compatibility with existing VoxShield pipeline
    def predict_file(self, audio_path: str):
        class ResultWrapper:
            def __init__(self, d):
                self.d = d
                self.success = d["prediction"] != "UNCERTAIN" or d.get("deepfake_score") is not None
            def to_dict(self):
                return self.d
        return ResultWrapper(self.predict(audio_path))


def get_voice_detector() -> VoiceDetector:
    """Singleton getter for the global VoiceDetector instance."""
    global _GLOBAL_DETECTOR
    if _GLOBAL_DETECTOR is None:
        _GLOBAL_DETECTOR = VoiceDetector()
        _GLOBAL_DETECTOR.load_model()
    return _GLOBAL_DETECTOR
