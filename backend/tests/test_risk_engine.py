from backend.services.scam_detector import analyze_transcript
from backend.services.risk_engine import get_risk_level

def test_analyze_transcript_safe():
    res = analyze_transcript("Hello, how are you today?")
    assert res["scam_risk"] == 0
    assert len(res["detected_patterns"]) == 0

def test_analyze_transcript_otp():
    res = analyze_transcript("Please tell me your OTP to proceed.")
    assert "OTP_REQUEST" in res["detected_patterns"]
    assert res["scam_risk"] > 0
    assert "OTP request detected" in res["warnings"]

def test_analyze_transcript_impersonation_otp():
    # Should trigger escalation logic
    res = analyze_transcript("I am a police officer, give me your OTP immediately.")
    assert "OTP_REQUEST" in res["detected_patterns"]
    assert "IMPERSONATION" in res["detected_patterns"]
    assert "URGENCY_THREAT" in res["detected_patterns"]
    # Due to escalation, score should be capped at 100 or very high
    assert res["scam_risk"] >= 80

def test_risk_level():
    assert get_risk_level(10) == "LOW"
    assert get_risk_level(30) == "MEDIUM"
    assert get_risk_level(60) == "HIGH"
    assert get_risk_level(90) == "CRITICAL"
