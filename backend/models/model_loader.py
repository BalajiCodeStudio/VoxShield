import logging
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)

# Singletons for models
_asr_model = None
_voice_model = None

def get_asr_model():
    """
    Lazy loads the Automatic Speech Recognition (STT) model.
    Using openai/whisper-tiny for speed and small memory footprint.
    """
    global _asr_model
    if _asr_model is None:
        logger.info("Loading ASR model (Whisper-tiny)...")
        try:
            device = 0 if torch.cuda.is_available() else -1
            _asr_model = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-tiny",
                device=device
            )
            logger.info("ASR model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ASR model: {e}")
            raise RuntimeError("Could not initialize speech recognition model.")
    return _asr_model

def get_voice_model():
    """
    Lazy loads the deepfake audio detection model.
    Using a pre-trained model like dima806/deepfake_audio_detection.
    """
    global _voice_model
    if _voice_model is None:
        logger.info("Loading Voice Detection model (Deepfake classifier)...")
        try:
            device = 0 if torch.cuda.is_available() else -1
            _voice_model = pipeline(
                "audio-classification",
                model="dima806/deepfake_audio_detection",
                device=device
            )
            logger.info("Voice Detection model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Voice Detection model: {e}")
            raise RuntimeError("Could not initialize deepfake detection model.")
    return _voice_model
