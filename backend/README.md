# VoxShield Backend

Backend for the VoxShield project: Real-time voice scam and AI-generated/deepfake voice detection system.
Designed to run locally for a 48-hour hackathon environment.

## Purpose
The backend receives short audio segments from the frontend/mobile app, analyzes them using real ML models (no hardcoded demo scores), and returns an aggregated risk profile (voice deepfake detection + speech-to-text contextual scam pattern detection).

## Architecture
- **FastAPI:** Core web framework.
- **Whisper (openai/whisper-tiny):** Used for real-time speech-to-text (transcription).
- **Deepfake Audio Detection (dima806/deepfake_audio_detection):** Audio classification to detect synthetic/AI voices.
- **Risk Engine:** Custom rule-based integration layer to combine model scores into a final threat level.

## Folder Structure
```
backend/
├── main.py              # FastAPI application entrypoint
├── requirements.txt     # Python dependencies
├── routes/              # API endpoints (/health, /analyze)
├── services/            # Core logic (voice_detector, scam_detector, risk_engine)
├── models/              # Lazy-loaded model singletons
├── utils/               # Audio preprocessing (librosa)
└── tests/               # Unit testing
```

## Python Version
Recommended: Python 3.9, 3.10, or 3.11.

## Installation

### 1. FFmpeg Requirement
You **must** have FFmpeg installed on your system for `librosa` and `soundfile` to decode audio formats like MP3 and M4A.
- **Windows:** Download from https://gyan.dev/ffmpeg/builds/ and add `bin` to your system PATH.
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### 2. Virtual Environment Setup
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Model Download
The models (`openai/whisper-tiny` and `dima806/deepfake_audio_detection`) are lazy-loaded. 
The first time you run a request, Hugging Face will download the weights (around 500MB total) and cache them in `~/.cache/huggingface/hub`. Subsequent requests will be much faster.

## How to Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
*(Use `--reload` during active development)*

## API Endpoints

### `GET /health`
Returns the status of the API.

### `POST /analyze`
Analyzes an uploaded audio file.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/analyze" -F "file=@test_audio.wav"
```

**Example Response:**
```json
{
  "voice_risk": 82,
  "scam_risk": 91,
  "overall_risk": 87,
  "level": "CRITICAL",
  "voice_analysis": {
    "is_ai_voice": true,
    "confidence": 82
  },
  "transcript": "Please tell me the OTP and approve the UPI request...",
  "detected_patterns": [
    "OTP_REQUEST",
    "UPI_PAYMENT",
    "URGENT_THREAT"
  ],
  "warnings": [
    "Possible AI-generated voice",
    "OTP request detected",
    "UPI/payment request detected"
  ]
}
```

## Network Testing (LAN)
To let the frontend mobile app connect to this backend from the same Wi-Fi network:
1. Find your computer's IP address (e.g., `ipconfig` on Windows -> IPv4 Address like `192.168.1.5`).
2. Run the server using `--host 0.0.0.0`.
3. The frontend can make requests to `http://192.168.1.5:8000/analyze`.

## Limitations (Hackathon Scope)
- No database storage; risk state is stateless per-request.
- Real-time streaming is simulated by the frontend uploading 5-10 second audio chunks sequentially.
- CPU inference can take 2-5 seconds depending on hardware. GPU acceleration (CUDA) is supported if PyTorch is installed with CUDA support.
