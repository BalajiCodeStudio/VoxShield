import numpy as np
import logging
from backend.models.model_loader import get_voice_model

logger = logging.getLogger(__name__)

def detect_ai_voice(waveform: np.ndarray, sr: int = 16000) -> dict:
    """
    Runs the deepfake detection model on the given waveform.
    Returns a dictionary with is_ai_voice, confidence, and voice_risk.
    """
    try:
        model = get_voice_model()
        
        # HuggingFace pipeline expects raw waveform array
        waveform_f32 = waveform.astype(np.float32)
        
        # The pipeline may return a list of dicts or list of lists depending on batching
        # Usually: [{'label': 'fake', 'score': 0.98}, {'label': 'real', 'score': 0.02}]
        results = model({"raw": waveform_f32, "sampling_rate": sr})
        
        # If the result is a nested list, extract the first item
        if isinstance(results, list) and len(results) > 0 and isinstance(results[0], list):
            results = results[0]

        fake_score = 0.0
        found_fake = False
        
        for res in results:
            label = res['label'].lower()
            if label in ['fake', 'spoof', 'synthetic', 'generated']:
                fake_score = res['score']
                found_fake = True
                break
                
        # If model only returns 'real' class
        if not found_fake:
            for res in results:
                label = res['label'].lower()
                if label in ['real', 'human', 'bonafide', 'original']:
                    fake_score = 1.0 - res['score']
                    break
                
        voice_risk = int(max(0.0, min(1.0, fake_score)) * 100)
        
        # Threshold for considering it an AI voice
        is_ai_voice = voice_risk >= 65
        confidence = voice_risk if is_ai_voice else (100 - voice_risk)
        
        return {
            "is_ai_voice": is_ai_voice,
            "confidence": confidence,
            "voice_risk": voice_risk
        }
    except Exception as e:
        logger.error(f"Error in voice detection: {e}")
        return {
            "is_ai_voice": False,
            "confidence": 0,
            "voice_risk": 0
        }
