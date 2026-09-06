"""
Voice Deepfake Detection Service for VoxShield Backend.
Integrates Member 1 Lightweight RawTFNet Voice Detector.
Supports single-instance memory loading, streaming detection, and Member 1 output contract.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Union, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy singleton
_DETECTOR = None


def _get_detector():
    global _DETECTOR
    if _DETECTOR is None:
        try:
            from ml.inference.detector import get_voice_detector
            _DETECTOR = get_voice_detector()
            logger.info("RawTFNet VoiceDetector initialized for VoxShield backend.")
        except Exception as e:
            logger.error(f"Failed to initialize VoiceDetector: {e}")
            raise
    return _DETECTOR


def detect_ai_voice(waveform: Union[np.ndarray, bytes], sr: int = 16000) -> Dict[str, Any]:
    """
    Runs the RawTFNet deepfake detection model on the given waveform.
    
    Returns standard VoxShield dictionary with:
    - is_ai_voice: bool
    - confidence: float (0 to 100)
    - voice_risk: int (0 to 100)
    - deepfake_score: float (0.0 to 1.0)
    - embedding_drift_score: null
    - model_version: str
    - prediction: "REAL" | "AI_GENERATED" | "UNCERTAIN"
    """
    try:
        detector = _get_detector()
        result = detector.predict(waveform)

        deepfake_score = result.get("deepfake_score")
        if deepfake_score is None:
            fake_prob = 0.0
            is_ai_voice = False
            confidence = 0
            voice_risk = 0
        else:
            fake_prob = float(deepfake_score)
            voice_risk = int(max(0.0, min(1.0, fake_prob)) * 100)
            is_ai_voice = result.get("prediction") == "AI_GENERATED" or voice_risk >= 50
            confidence = voice_risk if is_ai_voice else (100 - voice_risk)

        return {
            "is_ai_voice": is_ai_voice,
            "confidence": confidence,
            "voice_risk": voice_risk,
            "deepfake_score": round(fake_prob, 4),
            "embedding_drift_score": None,
            "model_version": f"{result.get('model_name', 'RawTFNet')}-{result.get('model_version', '1.0.0')}",
            "prediction": result.get("prediction", "UNCERTAIN"),
            "segments_analyzed": result.get("segments_analyzed", 0),
            "processing_time_ms": result.get("processing_time_ms", 0.0),
            "reason": result.get("reason", ""),
        }
    except Exception as e:
        logger.error(f"Error in voice detection: {e}", exc_info=True)
        return {
            "is_ai_voice": False,
            "confidence": 0,
            "voice_risk": 0,
            "deepfake_score": 0.0,
            "embedding_drift_score": None,
            "model_version": "RawTFNet-1.0.0",
            "prediction": "UNCERTAIN",
            "segments_analyzed": 0,
            "processing_time_ms": 0.0,
            "reason": f"Detection error: {str(e)}",
        }
