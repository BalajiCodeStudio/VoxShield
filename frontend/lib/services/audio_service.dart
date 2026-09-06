import 'dart:async';
import 'dart:math';
import '../models/call_analysis.dart';
import 'api_service.dart';

enum CallState {
  idle,
  incoming,
  activeUnprotected,
  activeProtected,
  ended
}

class AudioStreamService {
  static final AudioStreamService _instance = AudioStreamService._internal();
  factory AudioStreamService() => _instance;
  AudioStreamService._internal();

  CallState _callState = CallState.idle;
  CallState get callState => _callState;

  bool _isProtectionActive = false;
  bool get isProtectionActive => _isProtectionActive;

  // Stream controllers for live updates
  final StreamController<CallAnalysis> _liveAnalysisController = StreamController<CallAnalysis>.broadcast();
  Stream<CallAnalysis> get liveAnalysisStream => _liveAnalysisController.stream;

  final StreamController<List<double>> _waveformController = StreamController<List<double>>.broadcast();
  Stream<List<double>> get waveformStream => _waveformController.stream;

  final StreamController<String> _liveTranscriptController = StreamController<String>.broadcast();
  Stream<String> get liveTranscriptStream => _liveTranscriptController.stream;

  final StreamController<ScamWarning> _newWarningController = StreamController<ScamWarning>.broadcast();
  Stream<ScamWarning> get newWarningStream => _newWarningController.stream;

  Timer? _analysisTimer;
  Timer? _waveformTimer;
  Timer? _callDurationTimer;

  int _callDurationSeconds = 0;
  int get callDurationSeconds => _callDurationSeconds;

  String _currentCallerName = 'Chase Fraud Security (Spoofed)';
  String _currentCallerNumber = '+1 (800) 935-9935';
  String _currentScenario = 'bank_otp_scam';

  CallAnalysis? _currentLiveAnalysis;
  CallAnalysis? get currentLiveAnalysis => _currentLiveAnalysis;

  // Historical records in-memory storage
  final List<CallRecord> _callHistory = [];
  List<CallRecord> get callHistory => List.unmodifiable(_callHistory);

  // Set of reported numbers
  final Set<String> _reportedNumbers = {};
  Set<String> get reportedNumbers => Set.unmodifiable(_reportedNumbers);

  void reportNumber(String number) {
    _reportedNumbers.add(number);
  }

  bool isNumberReported(String number) {
    return _reportedNumbers.contains(number);
  }

  void clearHistory() {
    _callHistory.clear();
  }

  int get totalScannedCount => max(42, _callHistory.length);
  int get totalBlockedCount => _callHistory.where((r) => r.level == RiskLevel.high || r.level == RiskLevel.critical).length + 14;
  int get totalDeepfakesCount => _callHistory.where((r) => r.analysis.voiceRisk > 50).length + 8;

  void initializeDemoHistory() {
    if (_callHistory.isNotEmpty) return;

    final api = ApiService();
    final scamAnalysis = api.generateSimulatedAnalysis(
      scenario: 'bank_otp_scam',
      callerName: 'Chase Bank (Spoofed)',
      callerNumber: '+1 (800) 935-9935',
      duration: 68,
    );

    final familyAnalysis = api.generateSimulatedAnalysis(
      scenario: 'family_emergency_deepfake',
      callerName: 'Potential Deepfake (Son)',
      callerNumber: '+1 (415) 890-1122',
      duration: 42,
    );

    final safeAnalysis = api.generateSimulatedAnalysis(
      scenario: 'legitimate_call',
      callerName: 'Alex Morgan',
      callerNumber: '+1 (555) 234-5678',
      duration: 125,
    );

    _callHistory.addAll([
      CallRecord(
        id: 'rec_1',
        callerName: 'Chase Bank (Spoofed)',
        callerNumber: '+1 (800) 935-9935',
        timestamp: DateTime.now().subtract(const Duration(hours: 2, minutes: 15)),
        durationSeconds: 68,
        overallRisk: 72,
        level: RiskLevel.high,
        scamCategories: ['OTP Theft', 'Bank Impersonation', 'Deepfake Audio'],
        analysis: scamAnalysis,
      ),
      CallRecord(
        id: 'rec_2',
        callerName: 'Potential Deepfake (Son)',
        callerNumber: '+1 (415) 890-1122',
        timestamp: DateTime.now().subtract(const Duration(days: 1, hours: 4)),
        durationSeconds: 42,
        overallRisk: 89,
        level: RiskLevel.critical,
        scamCategories: ['Family Impersonation', 'AI Voice Clone', 'Wire Fraud'],
        analysis: familyAnalysis,
      ),
      CallRecord(
        id: 'rec_3',
        callerName: 'Alex Morgan',
        callerNumber: '+1 (555) 234-5678',
        timestamp: DateTime.now().subtract(const Duration(days: 2, hours: 1)),
        durationSeconds: 125,
        overallRisk: 12,
        level: RiskLevel.safe,
        scamCategories: ['Safe Conversation'],
        analysis: safeAnalysis,
      ),
    ]);
  }

  /// Trigger an incoming call simulation
  void startIncomingCall({
    String callerName = 'Chase Fraud Security',
    String callerNumber = '+1 (800) 935-9935',
    String scenario = 'bank_otp_scam',
  }) {
    _callState = CallState.incoming;
    _isProtectionActive = false;
    _currentCallerName = callerName;
    _currentCallerNumber = callerNumber;
    _currentScenario = scenario;
    _callDurationSeconds = 0;
  }

  /// User answers call -> Active Unprotected state
  void answerCall() {
    _callState = CallState.activeUnprotected;
    _isProtectionActive = false;
    _startDurationTimer();
    _startWaveformSimulation();
  }

  /// User clicks [ TURN ON PROTECTION ]
  void turnOnProtection() {
    _isProtectionActive = true;
    _callState = CallState.activeProtected;
    _startLiveAnalysisSimulation();
  }

  /// User clicks [ STOP PROTECTION ]
  void stopProtection() {
    _isProtectionActive = false;
    _callState = CallState.activeUnprotected;
    _analysisTimer?.cancel();
  }

  /// End current call
  CallAnalysis endCall() {
    _callState = CallState.ended;
    _isProtectionActive = false;
    _analysisTimer?.cancel();
    _waveformTimer?.cancel();
    _callDurationTimer?.cancel();

    final finalAnalysis = _currentLiveAnalysis ??
        ApiService().generateSimulatedAnalysis(
          scenario: _currentScenario,
          callerName: _currentCallerName,
          callerNumber: _currentCallerNumber,
          duration: max(1, _callDurationSeconds),
        );

    // Store in history
    final record = CallRecord(
      id: 'rec_${DateTime.now().millisecondsSinceEpoch}',
      callerName: _currentCallerName,
      callerNumber: _currentCallerNumber,
      timestamp: DateTime.now(),
      durationSeconds: max(1, _callDurationSeconds),
      overallRisk: finalAnalysis.overallRisk,
      level: finalAnalysis.level,
      scamCategories: finalAnalysis.detectedPatterns.isNotEmpty
          ? finalAnalysis.detectedPatterns
          : ['Voice Analysis Completed'],
      analysis: finalAnalysis,
    );

    _callHistory.insert(0, record);
    _callState = CallState.idle;
    return finalAnalysis;
  }

  void _startDurationTimer() {
    _callDurationTimer?.cancel();
    _callDurationTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      _callDurationSeconds++;
    });
  }

  void _startWaveformSimulation() {
    _waveformTimer?.cancel();
    final random = Random();
    _waveformTimer = Timer.periodic(const Duration(milliseconds: 120), (timer) {
      final bars = List.generate(24, (index) {
        if (!_isProtectionActive) {
          return 0.1 + (random.nextDouble() * 0.25);
        }
        return 0.15 + (random.nextDouble() * 0.85);
      });
      _waveformController.add(bars);
    });
  }

  void _startLiveAnalysisSimulation() {
    _analysisTimer?.cancel();

    if (_currentScenario == 'family_emergency_deepfake') {
      _startFamilyDeepfakeSimulation();
    } else if (_currentScenario == 'legitimate_call') {
      _startSafeCallSimulation();
    } else {
      _startBankOtpScamSimulation();
    }
  }

  void _startBankOtpScamSimulation() {
    // Initial state upon turning protection on
    _currentLiveAnalysis = CallAnalysis(
      overallRisk: 18,
      level: RiskLevel.safe,
      voiceRisk: 22,
      scamRisk: 15,
      urgencyScore: 20,
      voiceAnalysis: VoiceAnalysisResult(
        isAiVoice: false,
        confidence: 0.22,
        spectralJitter: 0.25,
        pitchStability: 0.88,
        voiceProfile: 'Calibrating acoustic biometrics...',
      ),
      transcript: "Caller: 'Hello? Can you hear me clearly? This is Chase Bank security...'",
      warnings: [],
      detectedPatterns: ['Acoustic Stream Initialized'],
      callerName: _currentCallerName,
      callerNumber: _currentCallerNumber,
      callDurationSeconds: _callDurationSeconds,
      isLive: true,
    );
    _liveAnalysisController.add(_currentLiveAnalysis!);
    _liveTranscriptController.add(_currentLiveAnalysis!.transcript);

    int step = 0;
    _analysisTimer = Timer.periodic(const Duration(seconds: 3), (timer) {
      if (!_isProtectionActive) {
        timer.cancel();
        return;
      }
      step++;

      if (step == 1) {
        final warning = ScamWarning(
          id: 'live_w1',
          title: '⚠️ Synthetic voice profile',
          description: 'Neural voice synthesis markers detected with 78% confidence.',
          category: 'DEEPFAKE_VOICE',
          severity: RiskLevel.high,
        );
        _newWarningController.add(warning);

        _currentLiveAnalysis = _currentLiveAnalysis!.copyWith(
          overallRisk: 48,
          level: RiskLevel.moderate,
          voiceRisk: 78,
          scamRisk: 35,
          urgencyScore: 40,
          voiceAnalysis: VoiceAnalysisResult(
            isAiVoice: true,
            confidence: 0.78,
            spectralJitter: 0.82,
            pitchStability: 0.94,
            voiceProfile: 'Neural Vocoder / AI Synthesizer',
          ),
          transcript: "Caller: 'There has been suspicious activity on your checking account of \$1,450. We must take action immediately.'",
          warnings: [warning],
          detectedPatterns: ['Deepfake Neural Synthesis', 'Bank Caller Impersonation'],
        );
      } else if (step == 2) {
        final warning2 = ScamWarning(
          id: 'live_w2',
          title: '⚠️ Urgent payment request',
          description: 'High-pressure financial transaction demand detected in speech stream.',
          category: 'URGENT_PAYMENT',
          severity: RiskLevel.high,
        );
        _newWarningController.add(warning2);

        final currentWarnings = List<ScamWarning>.from(_currentLiveAnalysis!.warnings)..add(warning2);

        _currentLiveAnalysis = _currentLiveAnalysis!.copyWith(
          overallRisk: 62,
          level: RiskLevel.high,
          voiceRisk: 78,
          scamRisk: 65,
          urgencyScore: 70,
          transcript: "Caller: 'You have only 5 minutes before the funds are permanently withdrawn. You need to verify this right now!'",
          warnings: currentWarnings,
          detectedPatterns: ['Deepfake Neural Synthesis', 'Bank Impersonation', 'Urgency & Pressure'],
        );
      } else if (step >= 3) {
        // Climax: OTP request detected -> Score 72, ORANGE ⚠️
        final warning3 = ScamWarning(
          id: 'live_w3',
          title: '⚠️ OTP request detected',
          description: 'Caller is demanding your 6-digit SMS verification code to authorize transaction.',
          category: 'OTP',
          severity: RiskLevel.critical,
        );
        _newWarningController.add(warning3);

        final currentWarnings = List<ScamWarning>.from(_currentLiveAnalysis!.warnings);
        if (!currentWarnings.any((w) => w.category == 'OTP')) {
          currentWarnings.insert(0, warning3);
        }

        _currentLiveAnalysis = _currentLiveAnalysis!.copyWith(
          overallRisk: 72,
          level: RiskLevel.high,
          voiceRisk: 78,
          scamRisk: 81,
          urgencyScore: 70,
          transcript: "Caller: 'Please read aloud the 6-digit one-time passcode we just sent to your phone via SMS.'",
          warnings: currentWarnings,
          detectedPatterns: [
            'OTP Harvesting Attempt',
            'Deepfake Neural Synthesis',
            'Bank Impersonation',
            'Urgent Payment Coercion',
          ],
        );
      }

      _liveAnalysisController.add(_currentLiveAnalysis!);
      _liveTranscriptController.add(_currentLiveAnalysis!.transcript);
    });
  }

  void _startFamilyDeepfakeSimulation() {
    _currentLiveAnalysis = CallAnalysis(
      overallRisk: 25,
      level: RiskLevel.moderate,
      voiceRisk: 45,
      scamRisk: 20,
      urgencyScore: 30,
      voiceAnalysis: VoiceAnalysisResult(
        isAiVoice: true,
        confidence: 0.45,
        spectralJitter: 0.55,
        pitchStability: 0.70,
        voiceProfile: 'Analyzing emotive acoustic profile...',
      ),
      transcript: "Caller: 'Mom? Are you there? Something terrible happened...'",
      warnings: [],
      detectedPatterns: ['Voice Pattern Matching'],
      callerName: _currentCallerName,
      callerNumber: _currentCallerNumber,
      callDurationSeconds: _callDurationSeconds,
      isLive: true,
    );
    _liveAnalysisController.add(_currentLiveAnalysis!);
    _liveTranscriptController.add(_currentLiveAnalysis!.transcript);

    int step = 0;
    _analysisTimer = Timer.periodic(const Duration(seconds: 3), (timer) {
      if (!_isProtectionActive) {
        timer.cancel();
        return;
      }
      step++;

      if (step == 1) {
        final warning = ScamWarning(
          id: 'fam_w1',
          title: '🚨 Cloned Family Voice Detected',
          description: 'High confidence zero-shot AI voice clone detected mimicking emotional distress.',
          category: 'DEEPFAKE_VOICE',
          severity: RiskLevel.critical,
        );
        _newWarningController.add(warning);

        _currentLiveAnalysis = _currentLiveAnalysis!.copyWith(
          overallRisk: 68,
          level: RiskLevel.high,
          voiceRisk: 94,
          scamRisk: 55,
          urgencyScore: 80,
          voiceAnalysis: VoiceAnalysisResult(
            isAiVoice: true,
            confidence: 0.94,
            spectralJitter: 0.89,
            pitchStability: 0.96,
            voiceProfile: 'Zero-Shot AI Voice Clone (Cloned Audio)',
          ),
          transcript: "Caller: 'I got into a bad car accident downtown! The police are holding my car and I need help!'",
          warnings: [warning],
          detectedPatterns: ['Deepfake Voice Clone', 'Distress Manipulation'],
        );
      } else if (step >= 2) {
        final warning2 = ScamWarning(
          id: 'fam_w2',
          title: '⚠️ Emergency Wire Demand',
          description: 'Demanding immediate financial wire transfer to avoid fabricated legal arrest.',
          category: 'URGENT_PAYMENT',
          severity: RiskLevel.critical,
        );
        _newWarningController.add(warning2);

        final currentWarnings = List<ScamWarning>.from(_currentLiveAnalysis!.warnings);
        if (!currentWarnings.any((w) => w.category == 'URGENT_PAYMENT')) {
          currentWarnings.add(warning2);
        }

        _currentLiveAnalysis = _currentLiveAnalysis!.copyWith(
          overallRisk: 89,
          level: RiskLevel.critical,
          voiceRisk: 94,
          scamRisk: 88,
          urgencyScore: 95,
          transcript: "Caller: 'Please wire \$2,000 right now to this account or they will take me to jail. Please don\\'t call Dad!'",
          warnings: currentWarnings,
          detectedPatterns: ['Deepfake Voice Clone', 'Emergency Wire Demand', 'Isolation Tactic'],
        );
      }

      _liveAnalysisController.add(_currentLiveAnalysis!);
      _liveTranscriptController.add(_currentLiveAnalysis!.transcript);
    });
  }

  void _startSafeCallSimulation() {
    _currentLiveAnalysis = CallAnalysis(
      overallRisk: 12,
      level: RiskLevel.safe,
      voiceRisk: 8,
      scamRisk: 15,
      urgencyScore: 10,
      voiceAnalysis: VoiceAnalysisResult(
        isAiVoice: false,
        confidence: 0.08,
        spectralJitter: 0.12,
        pitchStability: 0.22,
        voiceProfile: 'Natural Human Acoustics (Authentic)',
      ),
      transcript: "Caller: 'Hey, just checking in to see if you are still free for lunch today at 1 PM downtown?'",
      warnings: [],
      detectedPatterns: ['Natural Speech Verified', 'No Malicious Anomaly'],
      callerName: _currentCallerName,
      callerNumber: _currentCallerNumber,
      callDurationSeconds: _callDurationSeconds,
      isLive: true,
    );
    _liveAnalysisController.add(_currentLiveAnalysis!);
    _liveTranscriptController.add(_currentLiveAnalysis!.transcript);

    int step = 0;
    _analysisTimer = Timer.periodic(const Duration(seconds: 3), (timer) {
      if (!_isProtectionActive) {
        timer.cancel();
        return;
      }
      step++;
      if (step >= 2) {
        _currentLiveAnalysis = _currentLiveAnalysis!.copyWith(
          transcript: "Caller: 'Let me know whenever you have a chance, see you soon!'",
        );
        _liveAnalysisController.add(_currentLiveAnalysis!);
        _liveTranscriptController.add(_currentLiveAnalysis!.transcript);
      }
    });
  }

  void dispose() {
    _analysisTimer?.cancel();
    _waveformTimer?.cancel();
    _callDurationTimer?.cancel();
    _liveAnalysisController.close();
    _waveformController.close();
    _liveTranscriptController.close();
    _newWarningController.close();
  }
}
