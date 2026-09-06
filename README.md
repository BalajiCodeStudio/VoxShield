# VoxShield — Real-Time On-Device AI Voice & Scam Protection

[![Flutter](https://img.shields.io/badge/Flutter-3.x-blue.svg)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6+-red.svg)](https://pytorch.org)
[![RawTFNet](https://img.shields.io/badge/Model-RawTFNet--0.178M-orange.svg)](https://huggingface.co/SpeechAntiSpoofingBenchmarks/RawTFNet)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**VoxShield** is a next-generation real-time phone call security system that protects users against AI voice clones, deepfake audio, and financial impersonation scams directly during live phone conversations.

---

## Architecture Overview

```
                        ┌───────────────────────────────┐
                        │        LIVE CALL AUDIO        │
                        └───────────────┬───────────────┘
                                        │
                ┌───────────────────────┴───────────────────────┐
                ▼                                               ▼
  ┌───────────────────────────┐                   ┌───────────────────────────┐
  │   MEMBER 1: AI VOICE      │                   │    MEMBER 2: ASR & SCAM   │
  │   DEEPFAKE DETECTOR       │                   │    CONTENT DETECTOR       │
  ├───────────────────────────┤                   ├───────────────────────────┤
  │ • Silero / Energy VAD     │                   │ • Whisper STT Engine      │
  │ • RawTFNet (0.178M params)│                   │ • Keyword Matching        │
  │ • EMA Temporal Smoothing  │                   │ • Pattern Scoring         │
  │ • ONNX Fast Inference     │                   │ • Risk Escalation         │
  └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                │                                               │
                │ deepfake_score                                │ scam_score
                │ is_ai_voice                                   │ scam_risk
                │                                               │ warnings
                └───────────────────────┬───────────────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │   MEMBER 3: MULTI-MODAL       │
                        │   RISK FUSION ENGINE          │
                        ├───────────────────────────────┤
                        │ • Dynamic Weight Fusion       │
                        │ • Combined Risk Score (0-100) │
                        │ • Warning Levels (LOW-CRIT)   │
                        └───────────────┬───────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │   MEMBER 4: REAL-TIME         │
                        │   FLUTTER CALL OVERLAY UI     │
                        ├───────────────────────────────┤
                        │ • Floating Live Call Overlay  │
                        │ • Color-Coded Risk Gauge      │
                        │ • Interactive Protection CTA  │
                        │ • Threat Analysis Cards       │
                        └───────────────────────────────┘
```

---

## Project Structure

```
VoxShield/
├── backend/                  # FastAPI Python backend server
│   ├── main.py               # API entrypoint & routes
│   ├── routes/               # /analyze & /health REST endpoints
│   ├── services/             # Core orchestrator services
│   │   ├── voice_detector.py # Member 1: Voice Deepfake Service
│   │   ├── scam_detector.py  # Member 2: Scam Content Analysis
│   │   ├── transcription.py  # Member 2: Whisper STT Service
│   │   └── risk_engine.py    # Member 3: Risk Fusion Engine
│   └── utils/                # Audio decoding, VAD, config & logging
├── ml/                       # Machine Learning Module (Member 1)
│   ├── configs/config.yaml   # RawTFNet & detector configuration
│   ├── inference/            # Production inference engine & ONNX runtime
│   │   ├── detector.py       # Single-instance VoiceDetector
│   │   ├── streaming_detector.py # Real-time audio stream buffer
│   │   ├── postprocessing.py # EMA smoother & hysteresis
│   │   └── models/rawtfnet.py# RawTFNet architecture & adapter
│   ├── evaluation/           # Benchmarking & evaluation suite
│   │   ├── benchmark.py      # Latency, RAM, P50/P95 benchmarks
│   │   ├── metrics.py        # EER, ROC-AUC, Precision, Recall, F1
│   │   ├── cross_generator.py# Generalization across synthetic generators
│   │   └── robustness.py     # Noise, MP3, bandpass stress tests
│   └── training/             # Training, evaluation & ONNX export
├── frontend/                 # Flutter mobile & web application (Member 4)
│   ├── lib/                  # Dart application code
│   │   ├── main.dart         # Flutter app entrypoint
│   │   ├── screens/          # Call, Home, Risk & History screens
│   │   ├── widgets/          # Risk meter, warning cards, voice status
│   │   └── services/         # API & Audio streaming services
│   └── pubspec.yaml          # Flutter dependencies
├── data/                     # Scam indicators and keyword datasets
└── tests/                    # End-to-end unit and integration tests
```

---

## Quick Start Guide

### 1. Backend & ML Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run Unit Tests
python -m pytest tests/ -v

# Run Model Benchmark
python ml/evaluation/benchmark.py

# Start Backend Server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup (Flutter)
```bash
cd frontend

# Install Flutter dependencies
flutter pub get

# Run on Chrome Web (Instant Preview)
flutter run -d chrome --web-port=3000

# Or Build Android APK
flutter build apk --debug
```

---

## Member Responsibilities

- **Member 1 (AI Voice Deepfake Detection):** RawTFNet lightweight detector (177,540 params, 0.87 MB), Silero/Energy VAD, ONNX acceleration, EMA smoothing, and evaluation suite.
- **Member 2 (ASR & Scam Detection):** Whisper Automatic Speech Recognition, transcript tokenization, scam keyword patterns, and urgency heuristic detection.
- **Member 3 (Multi-Modal Risk Fusion):** Fusion of deepfake scores and conversational scam indicators into a real-time 0–100 risk score and actionable threat warnings.
- **Member 4 (Frontend & Call Overlay):** High-performance Flutter UI with real-time risk gauges, warning banners, call simulation, and call history tracking.