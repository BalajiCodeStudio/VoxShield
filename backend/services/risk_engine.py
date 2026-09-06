import logging
from backend.utils.audio import load_and_preprocess_audio
from backend.services.voice_detector import detect_ai_voice
from backend.services.scam_detector import analyze_scam_content

logger = logging.getLogger(__name__)

def get_risk_level(score: int) -> str:
    """Maps numerical score to risk level."""
    if score < 25:
        return "LOW"
    elif score < 50:
        return "MEDIUM"
    elif score < 75:
        return "HIGH"
    return "CRITICAL"

def analyze_call(file_bytes: bytes) -> dict:
    """
    Main orchestration function.
    Preprocesses audio, runs voice and scam detection, and calculates final risk.
    """
    try:
        logger.info("Starting call analysis...")
        
        # 1. Preprocess Audio
        waveform = load_and_preprocess_audio(file_bytes, target_sr=16000)
        
        # 2. Run Voice Detector (Deepfake/AI detection)
        voice_result = detect_ai_voice(waveform)
        
        # 3. Run Scam Detector (STT + Pattern matching)
        scam_result = analyze_scam_content(waveform)
        
        # 4. Calculate Overall Risk
        voice_risk = voice_result["voice_risk"]
        scam_risk = scam_result["scam_risk"]
        
        # Base weight: 40% AI Voice, 60% Scam Content
        base_overall_risk = int((voice_risk * 0.4) + (scam_risk * 0.6))
        
        warnings = set(scam_result["warnings"])
        if voice_result["is_ai_voice"]:
            warnings.add("Possible AI-generated voice")
            
        # Risk Escalation Logic
        escalation_penalty = 0
        
        # If it's an AI voice AND they are asking for money/OTP, it's highly critical
        if voice_result["is_ai_voice"] and scam_risk > 30:
            escalation_penalty += 30
            warnings.add("CRITICAL: AI voice combined with scam patterns")
            
        overall_risk = min(100, base_overall_risk + escalation_penalty)
        
        level = get_risk_level(overall_risk)
        
        return {
            "voice_risk": voice_risk,
            "scam_risk": scam_risk,
            "overall_risk": overall_risk,
            "level": level,
            "voice_analysis": {
                "is_ai_voice": voice_result["is_ai_voice"],
                "confidence": voice_result["confidence"]
            },
            "transcript": scam_result["transcript"],
            "warnings": list(warnings),
            "detected_patterns": scam_result["detected_patterns"]
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze call: {e}")
        raise RuntimeError("Internal error during call analysis.")
