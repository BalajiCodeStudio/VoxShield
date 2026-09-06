"""
VoxShield - Audio Transcription Service
Module: Member 2 (Speech-to-Text)

Responsibility:
VOICE -> TEXT ONLY.
Converts incoming caller audio into clean transcripts for downstream NLP analysis.
Handles audio file paths, raw bytes, base64 data, and streaming chunks safely with robust error handling.
"""

import os
import io
import re
import base64
import logging
from typing import Dict, Any, Optional, Union

# Configure logger
logger = logging.getLogger("voxshield.transcription")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [Transcription]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _redact_sensitive_text(text: str) -> str:
    """Mask OTPs, CVVs, and card numbers from log strings to maintain privacy."""
    if not text:
        return text
    # Mask 4-8 digit isolated numbers (likely OTPs/PINs)
    redacted = re.sub(r"\b\d{4,8}\b", "[REDACTED_CODE]", text)
    # Mask card numbers (12-19 digits)
    redacted = re.sub(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b", "[REDACTED_CARD]", redacted)
    return redacted


class AudioTranscriber:
    """
    Speech-to-text transcription engine supporting file paths, in-memory bytes,
    base64 audio strings, and audio stream chunks.
    """

    def __init__(self, default_language: str = "en-US"):
        self.default_language = default_language
        self._sr_recognizer = None
        self._whisper_model = None
        self._init_available_backends()

    def _init_available_backends(self) -> None:
        """Dynamically detect and initialize available STT backend libraries without crashing."""
        # 1. Check for SpeechRecognition library
        try:
            import speech_recognition as sr
            self._sr_recognizer = sr.Recognizer()
            self._sr_module = sr
            logger.info("SpeechRecognition backend initialized successfully.")
        except ImportError:
            self._sr_recognizer = None
            self._sr_module = None

        # 2. Check for OpenAI Whisper or Faster-Whisper
        try:
            import whisper
            # Lazy load model on demand if needed
            self._whisper_module = whisper
            logger.info("Whisper backend detected.")
        except ImportError:
            self._whisper_module = None

    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes an audio file on disk (WAV, MP3, FLAC, M4A, etc.).

        Args:
            file_path: Path to the audio file.
            language: Optional language code (default: en-US).

        Returns:
            Structured dictionary with 'text', 'confidence', 'language', 'success', and 'error'.
        """
        if not file_path or not isinstance(file_path, str):
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or self.default_language,
                "success": False,
                "error": "Invalid or empty file path provided."
            }

        if not os.path.exists(file_path):
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or self.default_language,
                "success": False,
                "error": f"Audio file not found: {file_path}"
            }

        lang = language or self.default_language

        # Strategy 1: SpeechRecognition (WAV/AIFF/FLAC)
        if self._sr_recognizer and self._sr_module:
            try:
                with self._sr_module.AudioFile(file_path) as source:
                    audio_data = self._sr_recognizer.record(source)
                    text = self._sr_recognizer.recognize_google(audio_data, language=lang)
                    return {
                        "text": text.strip(),
                        "confidence": 0.95,
                        "language": lang,
                        "success": True,
                        "error": None
                    }
            except self._sr_module.UnknownValueError:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": lang,
                    "success": True,
                    "error": None
                }
            except Exception as e:
                logger.warning(f"SpeechRecognition error on file {file_path}: {e}")

        # Strategy 2: Whisper backend if available
        if self._whisper_module:
            try:
                if self._whisper_model is None:
                    self._whisper_model = self._whisper_module.load_model("base")
                result = self._whisper_model.transcribe(file_path)
                return {
                    "text": result.get("text", "").strip(),
                    "confidence": 0.92,
                    "language": result.get("language", lang),
                    "success": True,
                    "error": None
                }
            except Exception as e:
                logger.warning(f"Whisper error on file {file_path}: {e}")

        # Fallback when no audio driver or offline mock:
        return {
            "text": "",
            "confidence": 0.0,
            "language": lang,
            "success": False,
            "error": "No functional STT engine available or file format unsupported."
        }

    def transcribe_bytes(self, audio_bytes: bytes, language: Optional[str] = None, format_hint: str = "wav") -> Dict[str, Any]:
        """
        Transcribes raw audio bytes in memory.

        Args:
            audio_bytes: Binary audio data.
            language: Optional language code.
            format_hint: Audio format hint (default: 'wav').

        Returns:
            Structured dictionary with transcription results.
        """
        if not audio_bytes or not isinstance(audio_bytes, (bytes, bytearray)):
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or self.default_language,
                "success": False,
                "error": "Invalid or empty audio bytes provided."
            }

        lang = language or self.default_language

        if self._sr_recognizer and self._sr_module:
            try:
                audio_io = io.BytesIO(audio_bytes)
                with self._sr_module.AudioFile(audio_io) as source:
                    audio_data = self._sr_recognizer.record(source)
                    text = self._sr_recognizer.recognize_google(audio_data, language=lang)
                    return {
                        "text": text.strip(),
                        "confidence": 0.95,
                        "language": lang,
                        "success": True,
                        "error": None
                    }
            except self._sr_module.UnknownValueError:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": lang,
                    "success": True,
                    "error": None
                }
            except Exception as e:
                logger.warning(f"SpeechRecognition error on bytes: {e}")

        return {
            "text": "",
            "confidence": 0.0,
            "language": lang,
            "success": False,
            "error": "STT engine unavailable or audio byte stream unparseable."
        }

    def transcribe_base64(self, b64_audio: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribes base64-encoded audio payload from web/mobile client."""
        if not b64_audio or not isinstance(b64_audio, str):
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or self.default_language,
                "success": False,
                "error": "Invalid or empty base64 string."
            }

        try:
            # Strip data URI header if present (e.g. data:audio/wav;base64,...)
            if "," in b64_audio:
                b64_audio = b64_audio.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_audio)
            return self.transcribe_bytes(raw_bytes, language=language)
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "language": language or self.default_language,
                "success": False,
                "error": f"Base64 decoding failed: {str(e)}"
            }

    def transcribe_stream_chunk(self, chunk_bytes: bytes, session_id: Optional[str] = None, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes a streaming audio chunk for real-time call monitoring.
        """
        result = self.transcribe_bytes(chunk_bytes, language=language)
        if session_id:
            result["session_id"] = session_id
        return result


# Global default instance
_default_transcriber = AudioTranscriber()


def transcribe_audio(audio_source: Union[str, bytes, io.BytesIO], language: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Convenience function for transcribing audio from any supported source:
    - File path (str)
    - Base64 string (str)
    - Raw bytes (bytes)
    - BytesIO stream
    """
    if isinstance(audio_source, str):
        if os.path.exists(audio_source):
            return _default_transcriber.transcribe_file(audio_source, language=language)
        else:
            return _default_transcriber.transcribe_base64(audio_source, language=language)
    elif isinstance(audio_source, (bytes, bytearray)):
        return _default_transcriber.transcribe_bytes(audio_source, language=language)
    elif isinstance(audio_source, io.BytesIO):
        return _default_transcriber.transcribe_bytes(audio_source.getvalue(), language=language)
    else:
        return {
            "text": "",
            "confidence": 0.0,
            "language": language or "en-US",
            "success": False,
            "error": f"Unsupported audio source type: {type(audio_source)}"
        }


def transcribe_file(file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Convenience wrapper for file transcription."""
    return _default_transcriber.transcribe_file(file_path, language=language)


def transcribe_bytes(audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
    """Convenience wrapper for byte transcription."""
    return _default_transcriber.transcribe_bytes(audio_bytes, language=language)


def transcribe_stream_chunk(chunk_bytes: bytes, session_id: Optional[str] = None, language: Optional[str] = None) -> Dict[str, Any]:
    """Convenience wrapper for streaming audio chunk transcription."""
    return _default_transcriber.transcribe_stream_chunk(chunk_bytes, session_id=session_id, language=language)
