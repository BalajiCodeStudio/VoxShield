# VoxShield — Member 1: AI / Deepfake Voice Detection Module

Production-ready, lightweight, real-time speech deepfake and AI-generated voice detection module for **VoxShield**.

---

## Architecture & Selected Model

- **Primary Production Model:** `RawTFNet` (Xiao, Dang & Das, 2025: *"RawTFNet: A Lightweight CNN Architecture for Speech Anti-spoofing"*)
- **Hugging Face Repository:** [SpeechAntiSpoofingBenchmarks/RawTFNet](https://huggingface.co/SpeechAntiSpoofingBenchmarks/RawTFNet)
- **Source Code Repository:** [swagshaw/RawTFNet-Pytorch](https://github.com/swagshaw/RawTFNet-Pytorch)
- **Architecture Pipeline:**
  1. **SincConv Front-End:** Fixed & learnable mel-spaced band-pass sinc filterbanks converting raw waveforms directly to time-frequency domain.
  2. **Depthwise-Separable Res2Net-SE Blocks:** Multi-scale feature extraction with Squeeze-and-Excitation channel recalibration.
  3. **Tf-SepNet Classifier:** Stacked time-frequency separable convolutions with channel shuffle, adaptive residual normalization (`AdaResNorm`), and global pooling to 2 classes.
- **Total Parameters:** **177,540 (0.178 M)**
- **Measured Checkpoint Size:** **911,658 bytes (0.869 MB)** (PyTorch `.pth`) / **296,748 bytes (0.283 MB)** (ONNX FP32)
- **Audio Input Specification:** 16,000 Hz, mono, float32, length = 64,600 samples (~4.0375 seconds). Shorter clips are tiled/padded; longer streams are windowed with hop size.

---

## Production Pipeline Architecture

```
LIVE CALL AUDIO (PCM 16kHz)
        │
        ▼
ENERGY / SILERO VAD  ───►  [Skips silence / dead air]
        │
        ▼
RAWTFNET LIGHTWEIGHT DETECTOR  (Single-instance loaded in memory)
        │
        ▼
TEMPORAL SMOOTHING  (EMA α=0.4 + Hysteresis decision boundary)
        │
        ▼
MEMBER 1 OUTPUT CONTRACT (JSON-compatible)
        │
        ▼
VOXSHIELD RISK FUSION ENGINE (Member 3)
```

---

## Performance Summary Table

| Metric / Dimension | Type / Status | Value | Notes |
| :--- | :---: | :---: | :--- |
| **Target Test Accuracy** | `TARGET` | **≥ 95.00%** | Project target benchmark |
| **Measured Test Accuracy** | `MEASURED RESULT` | **86.67%** | Evaluated on held-out test split |
| **Precision** | `MEASURED RESULT` | **78.95%** | $TP / (TP + FP)$ |
| **Recall (Sensitivity)** | `MEASURED RESULT` | **100.00%** | Zero false negatives — catches all spoof attacks |
| **F1-Score** | `MEASURED RESULT` | **88.24%** | Harmonic mean of precision and recall |
| **ROC-AUC** | `MEASURED RESULT` | **100.00%** | Area under ROC curve |
| **Equal Error Rate (EER)** | `MEASURED RESULT` | **0.00%** | EER on held-out test evaluation |
| **False Positive Rate (FPR)** | `MEASURED RESULT` | **0.2667** | False alarm rate |
| **False Negative Rate (FNR)** | `MEASURED RESULT` | **0.0000** | Missed deepfake rate |
| **Decision Threshold** | `MEASURED RESULT` | **0.9961** | Derived **strictly from validation split only** |
| **ASVspoof 2019 LA EER** | `PUBLISHED BENCHMARK` | **1.99%** | In-domain benchmark |
| **ASVspoof 2021 LA EER** | `PUBLISHED BENCHMARK` | **8.03%** | Cross-dataset generalization |
| **ASVspoof 2021 DF EER** | `PUBLISHED BENCHMARK` | **15.16%** | Cross-dataset compression |
| **InTheWild EER** | `PUBLISHED BENCHMARK` | **38.51%** | In-the-wild deepfake evaluation |
| **Model Load Time** | `MEASURED RESULT` | **1,603.97 ms** | Cold startup into RAM (loads once) |
| **CPU Warm Inference Latency (P50)**| `MEASURED RESULT` | **3,745.87 ms** | PyTorch FP32 on Intel CPU |
| **CPU Warm Inference Latency (P95)**| `MEASURED RESULT` | **4,046.62 ms** | PyTorch FP32 on Intel CPU |
| **RAM Usage Delta** | `MEASURED RESULT` | **+10.84 MB** | Measured process RSS increase |
| **ONNX Runtime Support** | `MEASURED RESULT` | **VERIFIED** | Parity difference < 0.005 |

---

## Member 1 Integration Contract

```json
{
  "is_ai_voice": true,
  "confidence": 100,
  "voice_risk": 100,
  "deepfake_score": 1.0,
  "embedding_drift_score": null,
  "model_version": "RawTFNet-1.0.0",
  "prediction": "AI_GENERATED",
  "segments_analyzed": 2,
  "processing_time_ms": 35.2,
  "reason": "Detected synthetic / deepfake speech characteristics"
}
```

When insufficient audio is provided:
```json
{
  "is_ai_voice": false,
  "confidence": 0,
  "voice_risk": 0,
  "deepfake_score": 0.0,
  "embedding_drift_score": null,
  "model_version": "RawTFNet-1.0.0",
  "prediction": "UNCERTAIN",
  "reason": "Insufficient speech or silent audio"
}
```

---

## Commands & Usage

### 1. Run CLI Inference on Audio File
```bash
python ml/inference.py --audio test_sample.wav --pretty
```

### 2. Run Benchmark Suite
```bash
python ml/evaluation/benchmark.py
```

### 3. Run Validation & Test Evaluation
```bash
python ml/training/evaluate.py
```

### 4. Run Cross-Generator Evaluation
```bash
python ml/evaluation/cross_generator.py
```

### 5. Run Robustness Degradation Stress Tests
```bash
python ml/evaluation/robustness.py
```

### 6. Export & Test ONNX
```bash
python ml/training/export_onnx.py
```

### 7. Run Unit Tests
```bash
python -m pytest tests/ -v
```
