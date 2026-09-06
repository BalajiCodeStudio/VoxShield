# VoxShield Member 1: AI / Deepfake Voice Detection

A production-ready AI voice deepfake detection pipeline using pretrained speech anti-spoofing models from Hugging Face.

## Architecture

```
Audio Input
    │
    ▼
Preprocessing (16kHz mono, segmentation, validation)
    │
    ├──────────┬──────────┐
    ▼          ▼          ▼
W2V2-AASIST  XLSR-SLS   W2V2-Large-AntiDeepfake
 (ONNX)      (ONNX)     (ONNX)
    │          │          │
    ▼          ▼          ▼
   P1         P2         P3
    └──────────┬──────────┘
               ▼
        Ensemble Model
       (weighted avg / LR)
               ▼
        Threshold Classification
               ▼
    REAL / AI_GENERATED / UNCERTAIN
```

## Model Family Details

| Model | HF Repository | License | Score Semantics |
|-------|---------------|---------|----------------|
| W2V2-AASIST | SpeechAntiSpoofingBenchmarks/W2V2-AASIST | MIT | logits → softmax, index 1 = bona fide |
| XLSR-SLS | SpeechAntiSpoofingBenchmarks/XLSR-SLS | MIT | log-softmax, index 1 = bona fide |
| Wav2Vec2-Large-AntiDeepfake | SpeechAntiSpoofingBenchmarks/Wav2Vec2-Large-AntiDeepfake | CC-BY-NC-SA-4.0 | logits → softmax, index 1 = real |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run inference on an audio file
.venv/Scripts/python ml/inference.py --audio path/to/audio.wav --pretty

# Start the backend API
.venv/Scripts/python -m uvicorn backend.main:app --reload
```

## Installation

```bash
# 1. Create virtual environment
python -m venv .venv
.venv/Scripts/activate  # Windows

# 2. Install PyTorch with CUDA
pip install torch==2.4.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu124

# 3. Install remaining dependencies
pip install -r requirements.txt
```

## Dataset Preparation

1. Place real audio files in `ml/datasets/real/`
2. Place synthetic (AI-generated) audio in `ml/datasets/synthetic/`
3. Build metadata and splits:

```bash
.venv/Scripts/python ml/datasets/build_metadata.py
```

### ASVspoof Protocol Support

For ASVspoof datasets, provide the protocol file:

```bash
.venv/Scripts/python ml/datasets/build_metadata.py --asvspoof-protocol /path/to/protocol.txt
```

## Training

```bash
# Train with default backbone (wav2vec2-base)
.venv/Scripts/python ml/training/train.py

# Train with XLS-R 300M (W2V2-AASIST style)
.venv/Scripts/python ml/training/train_w2v2.py

# Train with XLS-R 300M (XLSR-SLS style)
.venv/Scripts/python ml/training/train_xlsr.py
```

## Evaluation

```bash
# Evaluate pretrained ONNX ensemble on dataset
.venv/Scripts/python ml/training/evaluate.py --pretrained
```

## ONNX Export

```bash
# Export fine-tuned model
.venv/Scripts/python ml/training/export_onnx.py --ckpt ml/models/best_checkpoint --output ml/models/voice_detector.onnx
```

## Backend API

```bash
# Start server
.venv/Scripts/python -m uvicorn backend.main:app --reload

# Preload models on startup (optional)
VOXSHIELD_PRELOAD_MODELS=1 .venv/Scripts/python -m uvicorn backend.main:app
```

### API Endpoints

#### POST /api/voice/analyze

Upload an audio file for deepfake detection.

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/voice/analyze \
  -F "audio=@sample.wav"
```

**Example Response (AI-Generated):**
```json
{
  "success": true,
  "prediction": "AI_GENERATED",
  "confidence": 0.94,
  "real_probability": 0.06,
  "fake_probability": 0.94,
  "model_agreement": 1.0,
  "segments_analyzed": 5,
  "processing_time_ms": 1420,
  "models": {
    "w2v2_aasist": 0.96,
    "xlsr_sls": 0.93
  },
  "audio_duration_seconds": 10.5
}
```

**Example Response (Real):**
```json
{
  "success": true,
  "prediction": "REAL",
  "confidence": 0.97,
  "real_probability": 0.97,
  "fake_probability": 0.03
}
```

#### GET /api/health

Returns system health status and model loading state.

## Accepted Audio Formats

- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- FLAC (.flac)
- OGG (.ogg)

## Configuration

All settings are in `ml/configs/config.yaml`. Key options:

- **segment_samples**: 64600 (~4.04s at 16kHz)
- **hop_samples**: 32000 (2s overlap)
- **inference.aggregation**: mean / median / max
- **ensemble.method**: logistic_regression / weighted_average
- **models.members.*.enabled**: toggle individual models

## Known Limitations

1. **Dataset required for training**: ASVspoof and similar datasets require registration. The pipeline works out-of-the-box for inference using pretrained ONNX checkpoints.
2. **Tertiary model license**: Wav2Vec2-Large-AntiDeepfake is CC-BY-NC-SA-4.0 (non-commercial use only). Disabled by default.
3. **GPU recommended**: Inference on CPU is possible but ~10x slower.
4. **No false certainty**: Low-confidence predictions return UNCERTAIN rather than forcing a binary decision.

## Testing

```bash
.venv/Scripts/python -m pytest tests/ -v
```
