import logging
import numpy as np
import re
from backend.models.model_loader import get_asr_model

logger = logging.getLogger(__name__)

# Weighted scam patterns (regex based for robustness)
SCAM_PATTERNS = {
    "OTP_REQUEST": {
        "regex": r"\b(otp|one time password|verification code|authentication code)\b",
        "weight": 40
    },
    "UPI_PAYMENT": {
        "regex": r"\b(upi|google pay|gpay|phonepe|paytm|qr code|collect request|approve payment|send money|transfer money)\b",
        "weight": 35
    },
    "BANKING_INFO": {
        "regex": r"\b(bank account|debit card|credit card|cvv|pin|atm|net banking)\b",
        "weight": 35
    },
    "URGENCY_THREAT": {
        "regex": r"\b(urgent|immediately|right now|blocked|closed|police|arrest|legal action|kyc expired|kyc verification)\b",
        "weight": 30
    },
    "IMPERSONATION": {
        "regex": r"\b(bank officer|police officer|cbi|government officer|customer care|courier|electricity department|telecom)\b",
        "weight": 25
    }
}

def analyze_scam_content(waveform: np.ndarray, sr: int = 16000) -> dict:
    """
    Transcribes audio and analyzes the transcript for scam patterns.
    """
    try:
        asr_model = get_asr_model()
        
        # Whisper model inference
        # The pipeline accepts numpy array if sampling rate matches its expectation (usually 16k)
        result = asr_model({"raw": waveform.astype(np.float32), "sampling_rate": sr})
        transcript = result.get("text", "").strip()
        
        return analyze_transcript(transcript)
    except Exception as e:
        logger.error(f"Error in scam detection: {e}")
        return {
            "scam_risk": 0,
            "transcript": "",
            "detected_patterns": [],
            "warnings": []
        }

def analyze_transcript(transcript: str) -> dict:
    """
    Rule-based engine to calculate scam risk from transcript.
    """
    text_lower = transcript.lower()
    
    detected_patterns = set()
    warnings = set()
    total_weight = 0
    
    for pattern_name, details in SCAM_PATTERNS.items():
        if re.search(details["regex"], text_lower):
            detected_patterns.add(pattern_name)
            total_weight += details["weight"]
            
            # Map specific patterns to user-friendly warnings
            if pattern_name == "OTP_REQUEST":
                warnings.add("OTP request detected")
            elif pattern_name == "UPI_PAYMENT":
                warnings.add("UPI/payment request detected")
            elif pattern_name == "URGENCY_THREAT":
                warnings.add("Urgent action or threat detected")
            elif pattern_name == "IMPERSONATION":
                warnings.add("Possible impersonation detected")
            elif pattern_name == "BANKING_INFO":
                warnings.add("Sensitive banking info requested")

    # Contextual escalation multipliers
    # Example: If they ask for OTP + Impersonation -> highly suspicious
    if "OTP_REQUEST" in detected_patterns and "IMPERSONATION" in detected_patterns:
        total_weight += 20
        warnings.add("High Risk: Impersonator requesting OTP")
        
    if "UPI_PAYMENT" in detected_patterns and "URGENCY_THREAT" in detected_patterns:
        total_weight += 25
        warnings.add("High Risk: Urgent payment demand")
        
    scam_risk = min(100, total_weight)
    
    return {
        "scam_risk": scam_risk,
        "transcript": transcript,
        "detected_patterns": list(detected_patterns),
        "warnings": list(warnings)
    }
