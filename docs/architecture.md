# VoxShield System Architecture

## Component Breakdown

1. **Member 1: AI Voice Deepfake Detection**
   - Model: `RawTFNet` (0.178M parameters, 0.87 MB).
   - Preprocessing: 16 kHz resample, mono conversion, energy/Silero VAD.
   - Inference: Sinc convolution filterbank + time-frequency separable convolutions.
   - Postprocessing: Exponential Moving Average (EMA) smoothing and hysteresis thresholding.

2. **Member 2: Conversational Scam Detection**
   - ASR: OpenAI Whisper-tiny for low-latency on-device transcription.
   - Heuristics: Pattern matching against `data/scam_patterns.json` and `data/keywords.json`.
   - Scoring: Weighted urgency and impersonation indicators.

3. **Member 3: Multi-Modal Risk Fusion Engine**
   - Fusion Algorithm: Weighted multi-modal risk scoring (40% Voice, 60% Scam Content + Escalation Multipliers).
   - Dynamic Risk Levels: `LOW` (<25), `MEDIUM` (25-49), `HIGH` (50-74), `CRITICAL` (>=75).

4. **Member 4: Flutter Mobile & Web Client**
   - UI: Modern dark glassmorphic design, dynamic risk gauge, call screen overlay, call logs.
   - Services: Audio recording, WebSocket/HTTP streaming to FastAPI backend.
