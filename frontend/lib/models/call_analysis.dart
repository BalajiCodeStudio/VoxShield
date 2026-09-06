import 'package:flutter/material.dart';

enum RiskLevel {
  safe,
  moderate,
  high,
  critical;

  static RiskLevel fromScore(int score) {
    if (score < 25) return RiskLevel.safe;
    if (score < 50) return RiskLevel.moderate;
    if (score < 75) return RiskLevel.high;
    return RiskLevel.critical;
  }

  static RiskLevel fromString(String? levelStr) {
    switch (levelStr?.toUpperCase()) {
      case 'LOW':
      case 'SAFE':
        return RiskLevel.safe;
      case 'MEDIUM':
      case 'MODERATE':
      case 'YELLOW':
        return RiskLevel.moderate;
      case 'HIGH':
      case 'ORANGE':
        return RiskLevel.high;
      case 'CRITICAL':
      case 'RED':
        return RiskLevel.critical;
      default:
        return RiskLevel.safe;
    }
  }

  String get label {
    switch (this) {
      case RiskLevel.safe:
        return 'SAFE';
      case RiskLevel.moderate:
        return 'MODERATE RISK';
      case RiskLevel.high:
        return 'HIGH RISK';
      case RiskLevel.critical:
        return 'CRITICAL SCAM';
    }
  }

  String get colorBadgeText {
    switch (this) {
      case RiskLevel.safe:
        return 'GREEN 🛡️';
      case RiskLevel.moderate:
        return 'YELLOW ⚠️';
      case RiskLevel.high:
        return 'ORANGE ⚠️';
      case RiskLevel.critical:
        return 'RED 🚨';
    }
  }

  Color get color {
    switch (this) {
      case RiskLevel.safe:
        return const Color(0xFF10B981); // Emerald Green
      case RiskLevel.moderate:
        return const Color(0xFFFBBF24); // Amber Yellow
      case RiskLevel.high:
        return const Color(0xFFF97316); // Orange
      case RiskLevel.critical:
        return const Color(0xFFEF4444); // Red
    }
  }

  Color get backgroundTint {
    switch (this) {
      case RiskLevel.safe:
        return const Color(0x1A10B981);
      case RiskLevel.moderate:
        return const Color(0x1AFBBF24);
      case RiskLevel.high:
        return const Color(0x1AF97316);
      case RiskLevel.critical:
        return const Color(0x1AEF4444);
    }
  }

  IconData get icon {
    switch (this) {
      case RiskLevel.safe:
        return Icons.verified_user_rounded;
      case RiskLevel.moderate:
        return Icons.info_outline_rounded;
      case RiskLevel.high:
        return Icons.warning_amber_rounded;
      case RiskLevel.critical:
        return Icons.gpp_bad_rounded;
    }
  }
}

class VoiceAnalysisResult {
  final bool isAiVoice;
  final double confidence;
  final double spectralJitter;
  final double pitchStability;
  final String voiceProfile;

  VoiceAnalysisResult({
    required this.isAiVoice,
    required this.confidence,
    this.spectralJitter = 0.82,
    this.pitchStability = 0.91,
    this.voiceProfile = 'Synthesized Vocoder Detected',
  });

  factory VoiceAnalysisResult.fromJson(Map<String, dynamic> json) {
    return VoiceAnalysisResult(
      isAiVoice: json['is_ai_voice'] ?? false,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      spectralJitter: (json['spectral_jitter'] as num?)?.toDouble() ?? 0.82,
      pitchStability: (json['pitch_stability'] as num?)?.toDouble() ?? 0.91,
      voiceProfile: json['voice_profile'] ?? (json['is_ai_voice'] == true ? 'AI Cloned Synthetic Voice' : 'Human Natural Acoustic'),
    );
  }

  Map<String, dynamic> toJson() => {
    'is_ai_voice': isAiVoice,
    'confidence': confidence,
    'spectral_jitter': spectralJitter,
    'pitch_stability': pitchStability,
    'voice_profile': voiceProfile,
  };
}

class ScamWarning {
  final String id;
  final String title;
  final String description;
  final String category; // 'OTP', 'URGENT_PAYMENT', 'BANK_IMPERSONATION', 'DEEPFAKE_VOICE', 'THREAT'
  final RiskLevel severity;
  final DateTime timestamp;

  ScamWarning({
    required this.id,
    required this.title,
    required this.description,
    required this.category,
    required this.severity,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  factory ScamWarning.fromRawString(String text) {
    RiskLevel severity = RiskLevel.high;
    String category = 'GENERAL';
    String lower = text.toLowerCase();

    if (lower.contains('otp') || lower.contains('pin') || lower.contains('password')) {
      category = 'OTP';
      severity = RiskLevel.critical;
    } else if (lower.contains('payment') || lower.contains('wire') || lower.contains('transfer') || lower.contains('money')) {
      category = 'URGENT_PAYMENT';
      severity = RiskLevel.high;
    } else if (lower.contains('ai') || lower.contains('deepfake') || lower.contains('synthetic') || lower.contains('cloned')) {
      category = 'DEEPFAKE_VOICE';
      severity = RiskLevel.critical;
    } else if (lower.contains('bank') || lower.contains('officer') || lower.contains('police') || lower.contains('irs') || lower.contains('fed')) {
      category = 'IMPERSONATION';
      severity = RiskLevel.high;
    }

    return ScamWarning(
      id: UniqueKey().toString(),
      title: text.startsWith('⚠️') ? text : '⚠️ $text',
      description: _getDefaultDescription(category, text),
      category: category,
      severity: severity,
    );
  }

  static String _getDefaultDescription(String category, String title) {
    switch (category) {
      case 'OTP':
        return 'The caller is attempting to illicitly extract a One-Time Password (OTP) or authentication credential.';
      case 'URGENT_PAYMENT':
        return 'High-pressure financial transaction demand detected. Legitimate organizations rarely demand instant wire transfers.';
      case 'DEEPFAKE_VOICE':
        return 'Acoustic waveform analysis indicates robotic jitter and neural vocoder frequencies matching cloned audio.';
      case 'IMPERSONATION':
        return 'The caller is posing as authority/bank personnel using standard social engineering scripts.';
      default:
        return 'Suspicious conversation patterns flagged by real-time NLP analysis.';
    }
  }

  IconData get icon {
    switch (category) {
      case 'OTP':
        return Icons.pin_drop_rounded;
      case 'URGENT_PAYMENT':
        return Icons.attach_money_rounded;
      case 'DEEPFAKE_VOICE':
        return Icons.record_voice_over_rounded;
      case 'IMPERSONATION':
        return Icons.badge_rounded;
      default:
        return Icons.warning_rounded;
    }
  }
}

class RiskTimelineEvent {
  final int secondOffset;
  final int score;
  final RiskLevel level;
  final String flagReason;
  final String transcriptSnippet;

  RiskTimelineEvent({
    required this.secondOffset,
    required this.score,
    required this.level,
    required this.flagReason,
    required this.transcriptSnippet,
  });

  String get timeFormatted {
    final minutes = (secondOffset ~/ 60).toString().padLeft(2, '0');
    final seconds = (secondOffset % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}

class CallAnalysis {
  final int overallRisk;
  final RiskLevel level;
  final int voiceRisk;
  final int scamRisk;
  final int urgencyScore;
  final VoiceAnalysisResult voiceAnalysis;
  final String transcript;
  final List<ScamWarning> warnings;
  final List<String> detectedPatterns;
  final List<RiskTimelineEvent> timeline;
  final List<String> recommendations;
  final String callerName;
  final String callerNumber;
  final int callDurationSeconds;
  final DateTime analyzedAt;
  final bool isLive;

  CallAnalysis({
    required this.overallRisk,
    required this.level,
    required this.voiceRisk,
    required this.scamRisk,
    this.urgencyScore = 65,
    required this.voiceAnalysis,
    required this.transcript,
    required this.warnings,
    required this.detectedPatterns,
    this.timeline = const [],
    this.recommendations = const [],
    this.callerName = 'Unknown Caller',
    this.callerNumber = '+1 (800) 555-0199',
    this.callDurationSeconds = 48,
    DateTime? analyzedAt,
    this.isLive = false,
  }) : analyzedAt = analyzedAt ?? DateTime.now();

  factory CallAnalysis.fromJson(Map<String, dynamic> json, {String? callerName, String? callerNumber, int duration = 0}) {
    final overall = json['overall_risk'] as int? ?? 0;
    final levelStr = json['level'] as String? ?? 'LOW';
    final voiceRisk = json['voice_risk'] as int? ?? 0;
    final scamRisk = json['scam_risk'] as int? ?? 0;
    final urgency = json['urgency_score'] as int? ?? ((scamRisk * 0.9).round());

    final voiceMap = json['voice_analysis'] as Map<String, dynamic>? ?? {};
    final voiceResult = VoiceAnalysisResult.fromJson(voiceMap);

    final rawWarnings = (json['warnings'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];
    final warningsList = rawWarnings.map((w) => ScamWarning.fromRawString(w)).toList();

    final patterns = (json['detected_patterns'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [];

    final recs = <String>[];
    if (overall >= 75) {
      recs.add('🚨 Terminate call immediately. Do NOT verify identity over this channel.');
      recs.add('🔒 If OTP was shared, immediately lock your bank account & cards.');
      recs.add('📞 Call the official organization number directly from their verified website.');
    } else if (overall >= 50) {
      recs.add('⚠️ Exercise caution. Do not share two-factor codes, passwords, or personal details.');
      recs.add('❓ Ask the caller to provide a case ticket ID and state you will call back.');
    } else {
      recs.add('✅ No severe threat patterns detected. Normal conversation verified.');
    }

    return CallAnalysis(
      overallRisk: overall,
      level: RiskLevel.fromString(levelStr),
      voiceRisk: voiceRisk,
      scamRisk: scamRisk,
      urgencyScore: urgency,
      voiceAnalysis: voiceResult,
      transcript: json['transcript'] ?? '',
      warnings: warningsList,
      detectedPatterns: patterns,
      timeline: _buildDefaultTimeline(duration, overall),
      recommendations: recs,
      callerName: callerName ?? 'Unknown Caller',
      callerNumber: callerNumber ?? '+1 (888) 234-9001',
      callDurationSeconds: duration,
      analyzedAt: DateTime.now(),
    );
  }

  static List<RiskTimelineEvent> _buildDefaultTimeline(int duration, int score) {
    final list = <RiskTimelineEvent>[];
    list.add(RiskTimelineEvent(
      secondOffset: 0,
      score: 12,
      level: RiskLevel.safe,
      flagReason: 'Call Connected & Baseline Calibrated',
      transcriptSnippet: 'Hello, this is officer Jenkins from National Bank Fraud Dept...',
    ));
    if (duration >= 8) {
      list.add(RiskTimelineEvent(
        secondOffset: 8,
        score: (score * 0.45).round(),
        level: RiskLevel.moderate,
        flagReason: 'Acoustic AI synthesis markers detected',
        transcriptSnippet: 'Your debit card has been frozen due to suspicious activity.',
      ));
    }
    if (duration >= 18) {
      list.add(RiskTimelineEvent(
        secondOffset: 18,
        score: (score * 0.8).round(),
        level: score > 50 ? RiskLevel.high : RiskLevel.moderate,
        flagReason: 'Urgency & Fear Tactics Employed',
        transcriptSnippet: 'You must authorize instant cancellation or transfer money now.',
      ));
    }
    if (duration >= 28 && score >= 60) {
      list.add(RiskTimelineEvent(
        secondOffset: 28,
        score: score,
        level: RiskLevel.fromScore(score),
        flagReason: 'Direct OTP & Credential Harvesting attempt',
        transcriptSnippet: 'Please read aloud the 6-digit passcode we just sent to your SMS.',
      ));
    }
    return list;
  }

  CallAnalysis copyWith({
    int? overallRisk,
    RiskLevel? level,
    int? voiceRisk,
    int? scamRisk,
    int? urgencyScore,
    VoiceAnalysisResult? voiceAnalysis,
    String? transcript,
    List<ScamWarning>? warnings,
    List<String>? detectedPatterns,
    List<RiskTimelineEvent>? timeline,
    List<String>? recommendations,
    String? callerName,
    String? callerNumber,
    int? callDurationSeconds,
    bool? isLive,
  }) {
    return CallAnalysis(
      overallRisk: overallRisk ?? this.overallRisk,
      level: level ?? this.level,
      voiceRisk: voiceRisk ?? this.voiceRisk,
      scamRisk: scamRisk ?? this.scamRisk,
      urgencyScore: urgencyScore ?? this.urgencyScore,
      voiceAnalysis: voiceAnalysis ?? this.voiceAnalysis,
      transcript: transcript ?? this.transcript,
      warnings: warnings ?? this.warnings,
      detectedPatterns: detectedPatterns ?? this.detectedPatterns,
      timeline: timeline ?? this.timeline,
      recommendations: recommendations ?? this.recommendations,
      callerName: callerName ?? this.callerName,
      callerNumber: callerNumber ?? this.callerNumber,
      callDurationSeconds: callDurationSeconds ?? this.callDurationSeconds,
      analyzedAt: analyzedAt,
      isLive: isLive ?? this.isLive,
    );
  }
}

class CallRecord {
  final String id;
  final String callerName;
  final String callerNumber;
  final DateTime timestamp;
  final int durationSeconds;
  final int overallRisk;
  final RiskLevel level;
  final List<String> scamCategories;
  final CallAnalysis analysis;

  CallRecord({
    required this.id,
    required this.callerName,
    required this.callerNumber,
    required this.timestamp,
    required this.durationSeconds,
    required this.overallRisk,
    required this.level,
    required this.scamCategories,
    required this.analysis,
  });

  String get durationFormatted {
    final minutes = (durationSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (durationSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}

class AppSettings {
  bool isOverlayEnabled;
  bool autoProtectOnCall;
  bool showLiveTranscript;
  bool alertSounds;
  bool vibrationAlert;
  int sensitivityThreshold; // 0 (strict) to 100 (relaxed)
  String backendUrl;

  AppSettings({
    this.isOverlayEnabled = true,
    this.autoProtectOnCall = false,
    this.showLiveTranscript = true,
    this.alertSounds = true,
    this.vibrationAlert = true,
    this.sensitivityThreshold = 70,
    this.backendUrl = 'http://10.0.2.2:8000',
  });
}
