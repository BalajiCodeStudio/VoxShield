import librosa
import tempfile
import os
import numpy as np
import logging

logger = logging.getLogger(__name__)

def load_and_preprocess_audio(audio_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    """
    Loads audio from bytes, converts to mono, resamples to target_sr, 
    and normalizes the waveform.
    """
    # Create a temporary file to save the uploaded audio robustly
    fd, temp_path = tempfile.mkstemp(suffix=".tmp")
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(audio_bytes)
            
        # librosa.load automatically converts to mono and resamples
        y, sr = librosa.load(temp_path, sr=target_sr, mono=True)
        
        # Normalize the waveform
        if len(y) > 0:
            max_val = np.abs(y).max()
            if max_val > 0:
                y = y / max_val
                
        return y
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise ValueError("Could not decode audio file. Ensure it is a valid audio format.")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_path}: {e}")
