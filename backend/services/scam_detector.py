"""
VoxShield - Scam / NLP Detection Service
Module: Member 2 (Scam / NLP Detection)

Responsibility:
Analyzes speech transcripts using NLP and rule-based contextual pattern matching.
Detects scam indicators, extracts keywords and behavior patterns, evaluates intent/context,
computes a normalized 0-100 risk score, determines scam types, and provides explainable insights.
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logger
logger = logging.getLogger("voxshield.scam_detector")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [ScamDetector]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Risk Threshold Constants
SAFE_THRESHOLD_MAX = 29
SUSPICIOUS_THRESHOLD_MAX = 59
HIGH_RISK_THRESHOLD_MIN = 60

# Default file paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "data"))
KEYWORDS_DEFAULT_PATH = os.path.join(DEFAULT_DATA_DIR, "keywords.json")
PATTERNS_DEFAULT_PATH = os.path.join(DEFAULT_DATA_DIR, "scam_patterns.json")

# In-memory caches to ensure low latency and high-performance repeated calls
_CACHED_KEYWORDS: Optional[Dict[str, List[str]]] = None
_CACHED_PATTERNS: Optional[Dict[str, Dict[str, Any]]] = None

# Weighted pattern definitions for compatibility
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


def _find_file_path(target_path: Optional[str], default_filename: str) -> str:
    """Helper to safely resolve JSON configuration file paths across different execution roots."""
    candidates = []
    if target_path:
        candidates.append(target_path)
    candidates.extend([
        os.path.join(DEFAULT_DATA_DIR, default_filename),
        os.path.join(os.getcwd(), "data", default_filename),
        os.path.join(os.getcwd(), "VoxShield", "data", default_filename),
        os.path.join(CURRENT_DIR, default_filename)
    ])
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return candidates[0] if candidates else default_filename


def load_keywords(filepath: Optional[str] = None, force_reload: bool = False) -> Dict[str, List[str]]:
    """
    Loads configurable keyword database from data/keywords.json.
    Caches the parsed result in memory for near-real-time streaming performance.
    """
    global _CACHED_KEYWORDS
    if _CACHED_KEYWORDS is not None and not force_reload and filepath is None:
        return _CACHED_KEYWORDS

    resolved_path = _find_file_path(filepath, "keywords.json")
    try:
        if os.path.exists(resolved_path):
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if filepath is None:
                        _CACHED_KEYWORDS = data
                    return data
    except Exception as e:
        logger.error(f"Error loading keywords from {resolved_path}: {e}")

    # Fallback default dictionary if file is missing or corrupted
    fallback = {
        "otp": ["otp", "one time password", "verification code", "security code"],
        "banking": ["bank account", "account blocked", "account suspended", "debit card", "kyc"],
        "payment": ["send money", "transfer money", "make a payment", "upi", "qr code"],
        "personal_information": ["aadhaar", "pan number", "cvv", "password"],
        "credentials": ["cvv", "atm pin", "upi pin", "password", "card details"],
        "urgency": ["immediately", "right now", "urgent", "urgently", "without delay"],
        "threats": ["police", "arrest", "legal action", "blocked", "frozen", "digital arrest"],
        "impersonation": ["calling from police", "cbi", "bank security department", "rbi"],
        "prize_reward": ["won a prize", "won a lottery", "lucky winner", "cash award"],
        "technical_support": ["install anydesk", "download teamviewer", "remote access", "apk"],
        "loan_investment": ["guaranteed return", "pre approved loan", "double your investment"],
        "account_suspension": ["account will be blocked", "account suspended", "card blocked"]
    }
    if filepath is None:
        _CACHED_KEYWORDS = fallback
    return fallback


def load_patterns(filepath: Optional[str] = None, force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Loads configurable scam patterns database from data/scam_patterns.json.
    Caches the parsed result in memory for near-real-time streaming performance.
    """
    global _CACHED_PATTERNS
    if _CACHED_PATTERNS is not None and not force_reload and filepath is None:
        return _CACHED_PATTERNS

    resolved_path = _find_file_path(filepath, "scam_patterns.json")
    try:
        if os.path.exists(resolved_path):
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if filepath is None:
                        _CACHED_PATTERNS = data
                    return data
    except Exception as e:
        logger.error(f"Error loading scam patterns from {resolved_path}: {e}")

    # Fallback default pattern dictionary
    fallback = {
        "otp_request": {
            "category": "otp",
            "scam_type": "Banking / OTP Scam",
            "patterns": ["tell me your otp", "share your otp", "give me the otp", "give me your otp", "send me your otp"],
            "risk": 35,
            "indicator": "OTP request",
            "explanation": "The caller is demanding a One-Time Password or authentication code.",
            "recommendation": "Never share your OTP with anyone."
        },
        "credential_theft": {
            "category": "credentials",
            "scam_type": "Credential Theft",
            "patterns": ["tell me your cvv", "tell me your atm pin", "share your password", "give me your card details"],
            "risk": 35,
            "indicator": "Banking credential request",
            "explanation": "The caller is attempting to extract private financial credentials.",
            "recommendation": "Never disclose CVV, PIN, or passwords."
        },
        "bank_threat": {
            "category": "banking",
            "scam_type": "Account Suspension Scam",
            "patterns": ["account will be blocked", "account has been blocked", "account will be closed", "account will be suspended"],
            "risk": 25,
            "indicator": "Account suspension threat",
            "explanation": "The caller is threatening immediate account deactivation.",
            "recommendation": "Verify with your bank branch directly."
        },
        "payment_request": {
            "category": "payment",
            "scam_type": "Payment Scam",
            "patterns": ["send money", "transfer money", "make a payment", "pay through upi", "scan the qr code to receive"],
            "risk": 25,
            "indicator": "Payment demand",
            "explanation": "The caller is directing you to transfer money or scan QR codes.",
            "recommendation": "Never send money to unverified callers."
        }
    }
    if filepath is None:
        _CACHED_PATTERNS = fallback
    return fallback


def clean_text(text: Optional[str]) -> str:
    """
    Cleans and normalizes transcript text for NLP analysis:
    - Lowercase conversion
    - Replaces special punctuation with spaces
    - Normalizes consecutive whitespace
    - Preserves semantic words, digits, and phrases
    """
    if not text or not isinstance(text, str):
        return ""

    cleaned = text.lower()
    # Normalize punctuation and non-alphanumeric chars to single spaces (preserve letters, digits, and basic whitespace)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # Collapse multiple whitespace characters
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def detect_keywords(cleaned_text: str, keywords_db: Optional[Dict[str, List[str]]] = None) -> Dict[str, List[str]]:
    """
    Scans the normalized text against categorized keywords.

    Returns:
        Dict mapping category name -> list of matched keyword phrases.
    """
    if not cleaned_text:
        return {}

    db = keywords_db if keywords_db is not None else load_keywords()
    matched: Dict[str, List[str]] = {}

    for category, terms in db.items():
        if not isinstance(terms, list):
            continue
        found = []
        for term in terms:
            term_clean = clean_text(term)
            if not term_clean:
                continue
            # Regex boundary matching for exact words / phrases
            pattern = r"(?<!\w)" + re.escape(term_clean) + r"(?!\w)"
            if re.search(pattern, cleaned_text):
                if term not in found:
                    found.append(term)
        if found:
            matched[category] = found

    return matched


def detect_patterns(cleaned_text: str, patterns_db: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Scans normalized text for configured behavioral scam patterns.

    Returns:
        List of matched pattern information dictionaries.
    """
    if not cleaned_text:
        return []

    db = patterns_db if patterns_db is not None else load_patterns()
    detected: List[Dict[str, Any]] = []

    for pattern_key, config in db.items():
        if not isinstance(config, dict):
            continue

        phrase_list = config.get("patterns", [])
        if not isinstance(phrase_list, list):
            continue

        matched_phrases = []
        for phrase in phrase_list:
            phrase_clean = clean_text(phrase)
            if not phrase_clean:
                continue
            pattern_regex = r"(?<!\w)" + re.escape(phrase_clean) + r"(?!\w)"
            if re.search(pattern_regex, cleaned_text):
                matched_phrases.append(phrase)

        if matched_phrases:
            detected.append({
                "key": pattern_key,
                "category": config.get("category", "general"),
                "scam_type": config.get("scam_type", "Suspicious Call"),
                "indicator": config.get("indicator", pattern_key.replace("_", " ").title()),
                "risk": int(config.get("risk", 20)),
                "explanation": config.get("explanation", ""),
                "recommendation": config.get("recommendation", ""),
                "matched_phrases": matched_phrases
            })

    return detected


def analyze_context(text: str, detected_keywords: Dict[str, List[str]], detected_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs context and intent analysis to differentiate real scam coercion from
    educational, inquiry, advisory, safe statement, or receipt contexts.
    
    Prevents false positives like:
    - "Never share your OTP with anyone."
    - "I received an OTP from my bank."
    - "The bank reported a new OTP scam."
    - "Can you explain how OTP verification works?"
    """
    cleaned = clean_text(text)

    # 1. Advisory & Negation Patterns (explicit warning or advice against sharing)
    advisory_patterns = [
        r"\b(?:never|do not|don'?t|should not|shouldn'?t)\s+(?:share|give|disclose|tell|send|enter|provide)\b",
        r"\b(?:beware of|caution against|warned customers|reported a new|reported another|scam alert|fraud awareness)\b",
        r"\b(?:safe banking|security tip|awareness|be careful with|fake call)\b"
    ]
    is_advisory = any(re.search(p, cleaned) for p in advisory_patterns)

    # 2. Inquiry / Educational intent (user asking for clarification or education)
    educational_patterns = [
        r"\b(?:can you|could you|how does|how do i|please)\s+(?:explain|describe|clarify|understand)\s+(?:how|what|why)?\b",
        r"\b(?:how (?:does|is) otp (?:work|generated|verified)|what is an? otp)\b"
    ]
    is_educational = any(re.search(p, cleaned) for p in educational_patterns)

    # 3. Benign Receipt / 1st-person victim statement (neutral statement of receiving an SMS or news)
    receipt_patterns = [
        r"\b(?:i|we)\s+(?:received|got|have received|saw|read)\s+(?:an?|the)?\s*(?:otp|message|sms|notification|call|news)\b",
        r"\b(?:the news|the bank|the newspaper|police)\s+(?:reported|published|stated|warned|advised)\b"
    ]
    is_benign_receipt = any(re.search(p, cleaned) for p in receipt_patterns)

    # 4. Aggressive Coercion / Direct Demand patterns
    demand_patterns = [
        r"\b(?:give me|tell me|send me|provide me|share with me|read out)\b",
        r"\b(?:immediately|right now|without delay|urgent|within \d+ minutes|last warning)\b",
        r"\b(?:or else|otherwise|or your account will|or legal action|face arrest)\b"
    ]
    has_direct_demand = any(re.search(p, cleaned) for p in demand_patterns)

    # 5. Extraction Intent: Caller targeting credentials or funds
    has_urgency = "urgency" in detected_keywords or any(p["category"] == "urgency" for p in detected_patterns)
    has_threat = "threats" in detected_keywords or "account_suspension" in detected_keywords or any(p["category"] in ("banking", "threats", "account_suspension") for p in detected_patterns)
    has_impersonation = "impersonation" in detected_keywords or any(p["category"] == "impersonation" for p in detected_patterns)
    has_credential_req = "otp" in detected_keywords or "credentials" in detected_keywords or any(p["category"] in ("otp", "credentials") for p in detected_patterns)
    has_payment_req = "payment" in detected_keywords or any(p["category"] == "payment" for p in detected_patterns)

    # Determine if text represents safe context
    is_safe_context = False
    if is_advisory or is_educational or is_benign_receipt:
        # If there's an explicit advisory/negation and NO coercive demand, treat as safe
        if not (has_direct_demand and has_threat):
            is_safe_context = True

    return {
        "is_safe_context": is_safe_context,
        "is_advisory": is_advisory,
        "is_educational": is_educational,
        "is_benign_receipt": is_benign_receipt,
        "has_direct_demand": has_direct_demand,
        "has_urgency": has_urgency,
        "has_threat": has_threat,
        "has_impersonation": has_impersonation,
        "has_credential_req": has_credential_req,
        "has_payment_req": has_payment_req
    }


def calculate_risk_score(detected_patterns: List[Dict[str, Any]], detected_keywords: Dict[str, List[str]], context_info: Dict[str, Any]) -> int:
    """
    Computes a normalized 0-100 risk score using multi-factor evidence weighting.
    Applies aggressive false-positive reduction for safe, educational, and advisory sentences.
    """
    # 1. False Positive suppression
    if context_info.get("is_safe_context", False):
        return 5

    # 2. If nothing detected at all
    if not detected_patterns and not detected_keywords:
        return 0

    score = 0

    # 3. Add base risk from matched patterns (sum with diminishing returns)
    pattern_risks = [p.get("risk", 20) for p in detected_patterns]
    if pattern_risks:
        pattern_risks.sort(reverse=True)
        # Highest risk pattern contributes 100%, second 80%, third 60%, rest 40%
        multipliers = [1.0, 0.8, 0.6, 0.4]
        for i, r in enumerate(pattern_risks):
            weight = multipliers[i] if i < len(multipliers) else 0.3
            score += int(r * weight)

    # 4. Contextual Synergy Multipliers
    has_urgency = context_info.get("has_urgency", False)
    has_threat = context_info.get("has_threat", False)
    has_impersonation = context_info.get("has_impersonation", False)
    has_credential_req = context_info.get("has_credential_req", False)
    has_payment_req = context_info.get("has_payment_req", False)
    has_prize_reward = "prize_reward" in detected_keywords or any(p["category"] == "prize_reward" for p in detected_patterns)
    has_tech_support = "technical_support" in detected_keywords or any(p["category"] == "technical_support" for p in detected_patterns)
    has_loan_invest = "loan_investment" in detected_keywords or any(p["category"] == "loan_investment" for p in detected_patterns)

    # Urgency + Threat combo (classic coercion)
    if has_urgency and has_threat:
        score += 20

    # Credential/OTP request + Threat (critical scam combination)
    if has_credential_req and has_threat:
        score += 30

    # Credential/OTP request + Urgency
    if has_credential_req and has_urgency:
        score += 25

    # Impersonation + Payment / Credentials / Threat
    if has_impersonation and (has_credential_req or has_payment_req or has_threat):
        score += 30

    # Advance-fee Prize scam: Prize lure + Payment/fee demand or money transfer
    if has_prize_reward and (has_payment_req or "pay" in detected_keywords.get("payment", []) or any("pay" in ph for p in detected_patterns for ph in p.get("matched_phrases", []))):
        score += 40

    # Tech Support scam: Remote access + threat/warning or standalone remote tool install
    if has_tech_support and (has_threat or has_credential_req or has_payment_req):
        score += 35
    elif any(p["key"] == "tech_support_remote_access" for p in detected_patterns):
        score = max(score, 65)

    # Investment / Loan scam + payment fee / guarantee
    if has_loan_invest and (has_payment_req or has_urgency):
        score += 35
    elif any(p["key"] == "investment_loan_scam" for p in detected_patterns):
        score = max(score, 65)

    # Direct OTP / Credential / Police demand standalone pattern boost
    if any(p["key"] in ("otp_request", "credential_theft", "government_police_impersonation") for p in detected_patterns):
        score = max(score, 65)

    # Pure keyword-only base contributions if no high-risk pattern matched
    if not detected_patterns:
        if "otp" in detected_keywords:
            score += 15
        if "credentials" in detected_keywords:
            score += 20
        if "threats" in detected_keywords:
            score += 15
        if "urgency" in detected_keywords:
            score += 10
        if "impersonation" in detected_keywords:
            score += 20
        if "prize_reward" in detected_keywords:
            score += 20
        if "payment" in detected_keywords:
            score += 10

    # Multi-pattern reinforcement bonus
    if len(detected_patterns) >= 2:
        score += 15

    # Bound strictly between 0 and 100
    final_score = max(0, min(100, score))
    return int(final_score)


def classify_risk(risk_score: int) -> Tuple[str, bool]:
    """
    Classifies risk score into risk level and boolean flag.
    - 0-29: SAFE / LOW (is_scam: False)
    - 30-59: SUSPICIOUS / MEDIUM (is_scam: False / caution)
    - 60-100: HIGH RISK (is_scam: True)
    """
    if risk_score <= SAFE_THRESHOLD_MAX:
        return "LOW", False
    elif risk_score <= SUSPICIOUS_THRESHOLD_MAX:
        return "MEDIUM", False
    else:
        return "HIGH", True


def determine_scam_type(detected_patterns: List[Dict[str, Any]], detected_keywords: Dict[str, List[str]]) -> str:
    """
    Identifies the most prominent scam classification based on detected evidence.
    """
    if detected_patterns:
        # Select the highest risk pattern's scam_type
        sorted_patterns = sorted(detected_patterns, key=lambda p: p.get("risk", 0), reverse=True)
        return sorted_patterns[0].get("scam_type", "Suspicious Call")

    # Keyword fallback classification
    if "otp" in detected_keywords:
        return "Banking / OTP Scam"
    if "credentials" in detected_keywords:
        return "Credential Theft"
    if "impersonation" in detected_keywords:
        return "Government / Authority Impersonation"
    if "prize_reward" in detected_keywords:
        return "Prize / Reward Scam"
    if "technical_support" in detected_keywords:
        return "Technical Support Scam"
    if "loan_investment" in detected_keywords:
        return "Investment / Loan Scam"
    if "payment" in detected_keywords:
        return "Payment Scam"
    if "threats" in detected_keywords or "account_suspension" in detected_keywords:
        return "Account Suspension Scam"

    return "Safe / Non-Scam"


def generate_explanation(
    scam_type: str,
    detected_patterns: List[Dict[str, Any]],
    detected_keywords: Dict[str, List[str]],
    risk_level: str,
    context_info: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Generates human-readable reason and actionable safety recommendations.
    """
    if context_info.get("is_safe_context", False) or risk_level == "LOW":
        reason = "The conversation contains benign or informational context without scam coercion or credential extraction."
        recommendation = "No threat detected. Continue to follow standard security practices."
        return reason, recommendation

    # Synthesize reasons from detected patterns
    reasons = []
    recommendations = []

    for p in detected_patterns:
        if p.get("explanation") and p["explanation"] not in reasons:
            reasons.append(p["explanation"])
        if p.get("recommendation") and p["recommendation"] not in recommendations:
            recommendations.append(p["recommendation"])

    if not reasons:
        if risk_level == "HIGH":
            reasons.append("The caller is using urgency, threats, or demanding sensitive financial credentials.")
        else:
            reasons.append("The conversation contains suspicious keywords or financial requests that warrant caution.")

    if not recommendations:
        if "otp" in detected_keywords or "credentials" in detected_keywords:
            recommendations.append("Never share OTPs, CVVs, PINs, or passwords with anyone over the phone.")
        elif "payment" in detected_keywords:
            recommendations.append("Do not transfer money or scan QR codes based on unsolicited calls.")
        else:
            recommendations.append("Do not share personal details. Verify independently with official service providers.")

    full_reason = " ".join(reasons)
    full_rec = " ".join(recommendations)
    return full_reason, full_rec


def analyze_text(text: Optional[str], session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main public analysis pipeline.
    
    Accepts raw transcript text, executes complete NLP & context-aware scam detection,
    and returns a clean, structured dictionary.
    
    Args:
        text: Raw caller transcript string.
        session_context: Optional context from streaming/previous chunks.
        
    Returns:
        Structured result matching VoxShield frontend and backend contracts.
    """
    # 1. Defensive input validation
    if text is None or not isinstance(text, str):
        return {
            "text": "",
            "cleaned_text": "",
            "risk_score": 0,
            "risk_level": "LOW",
            "is_scam": False,
            "scam_type": "Safe / Non-Scam",
            "detected_keywords": [],
            "detected_patterns": [],
            "keywords": [],
            "patterns": [],
            "indicators": [],
            "reason": "No text provided for analysis.",
            "recommendation": "Awaiting caller audio transcript.",
            "success": True,
            "error": None
        }

    raw_text = text.strip()
    if not raw_text:
        return {
            "text": "",
            "cleaned_text": "",
            "risk_score": 0,
            "risk_level": "LOW",
            "is_scam": False,
            "scam_type": "Safe / Non-Scam",
            "detected_keywords": [],
            "detected_patterns": [],
            "keywords": [],
            "patterns": [],
            "indicators": [],
            "reason": "Empty transcript.",
            "recommendation": "Awaiting caller voice input.",
            "success": True,
            "error": None
        }

    try:
        # 2. Text Normalization / NLP Preprocessing
        cleaned = clean_text(raw_text)

        # 3. Keyword Detection
        keyword_matches = detect_keywords(cleaned)
        all_flattened_keywords = []
        for kw_list in keyword_matches.values():
            for k in kw_list:
                if k not in all_flattened_keywords:
                    all_flattened_keywords.append(k)

        # 4. Pattern Detection
        pattern_matches = detect_patterns(cleaned)
        indicator_names = [p["indicator"] for p in pattern_matches]

        # 5. Context & Intent Analysis (False-positive mitigation)
        context_info = analyze_context(raw_text, keyword_matches, pattern_matches)

        # 6. Risk Scoring (0-100)
        risk_score = calculate_risk_score(pattern_matches, keyword_matches, context_info)

        # Merge with session history if streaming chunks are supplied
        if session_context and isinstance(session_context, dict):
            prev_score = session_context.get("accumulated_risk", 0)
            if prev_score > 0 and not context_info.get("is_safe_context", False):
                risk_score = max(risk_score, min(100, int(prev_score * 0.7 + risk_score * 0.5)))

        # 7. Classification
        risk_level, is_scam = classify_risk(risk_score)
        scam_type = determine_scam_type(pattern_matches, keyword_matches) if risk_score >= 30 else "Safe / Non-Scam"

        # 8. Explanation & Recommendations
        reason, recommendation = generate_explanation(scam_type, pattern_matches, keyword_matches, risk_level, context_info)

        return {
            "text": raw_text,
            "cleaned_text": cleaned,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "is_scam": is_scam,
            "scam_type": scam_type,
            "detected_keywords": all_flattened_keywords,
            "detected_patterns": indicator_names,
            "keywords": all_flattened_keywords,
            "patterns": indicator_names,
            "indicators": indicator_names,
            "context": context_info,
            "reason": reason,
            "recommendation": recommendation,
            "success": True,
            "error": None
        }

    except Exception as e:
        logger.error(f"Unexpected error during scam detection analysis: {e}", exc_info=True)
        return {
            "text": raw_text,
            "cleaned_text": clean_text(raw_text),
            "risk_score": 0,
            "risk_level": "LOW",
            "is_scam": False,
            "scam_type": "Unknown / Error",
            "detected_keywords": [],
            "detected_patterns": [],
            "keywords": [],
            "patterns": [],
            "indicators": [],
            "reason": "An error occurred during analysis.",
            "recommendation": "Please try analyzing the transcript again.",
            "success": False,
            "error": str(e)
        }


def analyze_transcript(transcript: str) -> Dict[str, Any]:
    """
    Bridge helper providing compatibility for callers expecting legacy/transcript format:
    returns 'scam_risk', 'warnings', 'detected_patterns', 'transcript', and all structured fields.
    """
    res = analyze_text(transcript)
    warnings = []
    if res.get("reason"):
        warnings.append(res["reason"])
    if res.get("recommendation"):
        warnings.append(res["recommendation"])
    
    return {
        "scam_risk": res.get("risk_score", 0),
        "transcript": transcript,
        "detected_patterns": res.get("detected_patterns", []),
        "warnings": warnings,
        **res
    }


def analyze_scam_content(waveform: Any, sr: int = 16000) -> Dict[str, Any]:
    """
    Transcribes audio waveform and analyzes transcript for scam indicators.
    """
    try:
        from backend.models.model_loader import get_asr_model
        asr_model = get_asr_model()
        import numpy as np
        if isinstance(waveform, np.ndarray):
            result = asr_model({"raw": waveform.astype(np.float32), "sampling_rate": sr})
            transcript = result.get("text", "").strip()
            return analyze_transcript(transcript)
    except Exception as e:
        logger.warning(f"ASR model audio analysis fallback: {e}")
    
    return {
        "scam_risk": 0,
        "transcript": "",
        "detected_patterns": [],
        "warnings": []
    }


def analyze_chunk(chunk_text: str, session_history: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Helper for streaming transcript chunks in near-real-time calls.
    Maintains session history across chunks.
    """
    history = session_history if session_history is not None else []
    full_conversation = " ".join(history + [chunk_text])
    result = analyze_text(full_conversation)
    result["current_chunk"] = chunk_text
    return result


def evaluate_dataset(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates detector performance on a labeled test dataset.
    Calculates Accuracy, Precision, Recall, F1 Score, False Positive Rate,
    False Negative Rate, and Confusion Matrix.
    
    Each test case must be: {"text": str, "expected_is_scam": bool}
    """
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for item in test_cases:
        text = item.get("text", "")
        expected = item.get("expected_is_scam", False)
        result = analyze_text(text)
        predicted = result.get("is_scam", False)

        if expected and predicted:
            tp += 1
        elif not expected and predicted:
            fp += 1
        elif not expected and not predicted:
            tn += 1
        elif expected and not predicted:
            fn += 1

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return {
        "total_samples": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "confusion_matrix": {
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn
        }
    }
