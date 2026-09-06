# VoxShield REST & WebSocket API Specification

## 1. Analyze Audio Endpoint

- **Method:** `POST`
- **Path:** `/analyze`
- **Content-Type:** `multipart/form-data`
- **Description:** Analyzes a call audio recording for deepfake voice indicators and scam conversation patterns.

### Request
- `file`: Audio file (`.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`)

### Response (`200 OK`)
```json
{
  "voice_risk": 95,
  "scam_risk": 80,
  "overall_risk": 92,
  "level": "CRITICAL",
  "voice_analysis": {
    "is_ai_voice": true,
    "confidence": 95
  },
  "transcript": "Hello, this is Bank security. Please verify your OTP immediately.",
  "warnings": [
    "Possible AI-generated voice",
    "CRITICAL: AI voice combined with scam patterns",
    "OTP Request Detected"
  ],
  "detected_patterns": [
    "Bank Security Impersonation",
    "Urgent Verification Request",
    "OTP Phishing"
  ]
}
```

---

## 2. Health Check Endpoint

- **Method:** `GET`
- **Path:** `/health`

### Response (`200 OK`)
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "models": {
    "voice_detector": "RawTFNet (Lightweight)",
    "asr": "Whisper-tiny"
  }
}
```
