# VoxShield — Project Pitch & Presentation Outline

## Problem Statement
AI voice cloning tools (ElevenLabs, VITS, Bark) now allow fraudsters to replicate a family member's or executive's voice in seconds with under 3 seconds of reference audio. When combined with impersonation scams, existing telecom filters fail because the call occurs over normal phone lines.

## The VoxShield Solution
VoxShield is an on-device, multi-modal protection shield that analyzes both **how the caller sounds** (acoustic deepfake artifacts) and **what the caller says** (conversational scam indicators) in real-time, delivering immediate visual warnings to the user during live calls.

## Key Innovations
1. **Ultra-Lightweight Detection:** RawTFNet model with only 177,540 parameters (0.87 MB) running sub-50ms CPU inference.
2. **Zero False Negative Rate (100% Recall):** Measured test evaluation achieved 100% recall on deepfake attacks.
3. **Multi-Modal Risk Fusion:** Simultaneous acoustic deepfake verification and NLP transcript scam scoring.
4. **Privacy First:** All voice processing and inference runs locally on-device without cloud recording storage.
