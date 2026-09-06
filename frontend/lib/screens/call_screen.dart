import 'dart:async';
import 'package:flutter/material.dart';
import '../models/call_analysis.dart';
import '../services/audio_service.dart';
import '../widgets/voice_status.dart';
import 'risk_screen.dart';

class CallScreen extends StatefulWidget {
  final String callerName;
  final String callerNumber;
  final String scenario;
  final AppSettings settings;

  const CallScreen({
    super.key,
    this.callerName = 'Chase Fraud Security (Suspicious)',
    this.callerNumber = '+1 (800) 935-9935',
    this.scenario = 'bank_otp_scam',
    required this.settings,
  });

  @override
  State<CallScreen> createState() => _CallScreenState();
}

class _CallScreenState extends State<CallScreen> with SingleTickerProviderStateMixin {
  final AudioStreamService _audioService = AudioStreamService();

  bool _isAnswered = false;
  bool _isMuted = false;
  bool _isSpeaker = true;
  bool _isOverlayMinimized = false;
  String _dialedKeypadDigits = '';

  late AnimationController _slideController;
  late Animation<Offset> _slideAnimation;

  StreamSubscription<CallAnalysis>? _analysisSub;
  StreamSubscription<String>? _transcriptSub;

  CallAnalysis? _liveAnalysis;
  String _liveTranscript = '';
  int _secondsElapsed = 0;
  Timer? _localTimer;

  @override
  void initState() {
    super.initState();

    _slideController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 550),
    );

    _slideAnimation = Tween<Offset>(
      begin: const Offset(-1.1, 0.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeOutCubic,
    ));

    _audioService.startIncomingCall(
      callerName: widget.callerName,
      callerNumber: widget.callerNumber,
      scenario: widget.scenario,
    );

    // Slide in notification automatically upon call arrival
    if (widget.settings.isOverlayEnabled) {
      Future.delayed(const Duration(milliseconds: 300), () {
        if (mounted) {
          _slideController.forward();
        }
      });
    }

    // Auto-protect if configured in settings
    if (widget.settings.autoProtectOnCall) {
      Future.delayed(const Duration(milliseconds: 600), () {
        if (mounted && !_isAnswered) {
          _answerCall();
          _activateProtection();
        }
      });
    }
  }

  void _answerCall() {
    setState(() {
      _isAnswered = true;
    });
    _audioService.answerCall();

    _localTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          _secondsElapsed++;
        });
      }
    });

    if (widget.settings.isOverlayEnabled && !_slideController.isCompleted) {
      _slideController.forward();
    }

    _subscribeToStreams();
  }

  void _subscribeToStreams() {
    _analysisSub = _audioService.liveAnalysisStream.listen((analysis) {
      if (mounted) {
        setState(() {
          _liveAnalysis = analysis;
        });
      }
    });

    _transcriptSub = _audioService.liveTranscriptStream.listen((text) {
      if (mounted) {
        setState(() {
          _liveTranscript = text;
        });
      }
    });
  }

  void _activateProtection() {
    if (!_isAnswered) {
      _answerCall();
    }
    _audioService.turnOnProtection();
    setState(() {});
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('🛡️ VoiceGuard Protection Activated: Real-time scan live.'),
        backgroundColor: Color(0xFF10B981),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _stopProtection() {
    _audioService.stopProtection();
    setState(() {});
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('⏸️ Protection Paused: Tap Turn On Protection to resume.'),
        backgroundColor: Color(0xFFF97316),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _endCall() {
    _localTimer?.cancel();
    _slideController.reverse();
    final finalAnalysis = _audioService.endCall();

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => RiskScreen(analysis: finalAnalysis),
      ),
    );
  }

  void _openKeypadModal() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F172A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setKeypadState) {
            return Container(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'DTMF In-Call Keypad',
                        style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close_rounded, color: Colors.white60),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E293B),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          _dialedKeypadDigits.isEmpty ? 'Touch keys to send tone...' : _dialedKeypadDigits,
                          style: TextStyle(
                            color: _dialedKeypadDigits.isEmpty ? Colors.white38 : const Color(0xFF38BDF8),
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 2,
                          ),
                        ),
                        if (_dialedKeypadDigits.isNotEmpty)
                          IconButton(
                            icon: const Icon(Icons.backspace_outlined, color: Colors.white60, size: 20),
                            onPressed: () {
                              setKeypadState(() {
                                _dialedKeypadDigits = _dialedKeypadDigits.substring(0, _dialedKeypadDigits.length - 1);
                              });
                            },
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Keypad grid
                  ...[
                    ['1', '2', '3'],
                    ['4', '5', '6'],
                    ['7', '8', '9'],
                    ['*', '0', '#'],
                  ].map((row) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: row.map((key) {
                          return InkWell(
                            onTap: () {
                              setKeypadState(() {
                                _dialedKeypadDigits += key;
                              });
                            },
                            borderRadius: BorderRadius.circular(30),
                            child: Container(
                              width: 58,
                              height: 58,
                              decoration: const BoxDecoration(
                                color: Color(0xFF1E293B),
                                shape: BoxShape.circle,
                              ),
                              child: Center(
                                child: Text(
                                  key,
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 22,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    );
                  }),
                  const SizedBox(height: 10),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  void dispose() {
    _localTimer?.cancel();
    _analysisSub?.cancel();
    _transcriptSub?.cancel();
    _slideController.dispose();
    super.dispose();
  }

  String _formatDuration(int totalSecs) {
    final mins = (totalSecs ~/ 60).toString().padLeft(2, '0');
    final secs = (totalSecs % 60).toString().padLeft(2, '0');
    return '$mins:$secs';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1D),
      body: SafeArea(
        child: Stack(
          children: [
            // Ambient Lighting
            Positioned(
              top: -60,
              right: -60,
              child: Container(
                width: 260,
                height: 260,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _audioService.isProtectionActive
                      ? (_liveAnalysis?.level.color.withValues(alpha: 0.12) ?? const Color(0xFFF97316).withValues(alpha: 0.12))
                      : const Color(0xFF3B82F6).withValues(alpha: 0.08),
                ),
              ),
            ),

            // Main UI
            Column(
              children: [
                _buildTopAppBar(),
                Expanded(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Column(
                      children: [
                        const SizedBox(height: 10),
                        _buildCallerProfile(),
                        const SizedBox(height: 16),

                        // Automatic Slide-In Notification Card
                        if (widget.settings.isOverlayEnabled)
                          _buildSlideInMenu(),

                        // Notice if user disabled overlay in settings
                        if (!widget.settings.isOverlayEnabled)
                          _buildOverlayDisabledNotice(),

                        const SizedBox(height: 14),

                        // Real-time voice biometrics waveform
                        if (_isAnswered && _audioService.isProtectionActive) ...[
                          VoiceStatusWidget(
                            voiceAnalysis: _liveAnalysis?.voiceAnalysis,
                            waveformStream: _audioService.waveformStream,
                            isLive: true,
                          ),
                          const SizedBox(height: 14),
                        ],

                        // Live Speech Transcript Box
                        if (_isAnswered && _audioService.isProtectionActive && widget.settings.showLiveTranscript)
                          _buildLiveTranscriptBox(),

                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),

                // Bottom Call Controls (Keypad, Mute, Speaker, Answer / End)
                _buildCallControls(),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopAppBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white70, size: 20),
            onPressed: () => Navigator.pop(context),
          ),
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: _audioService.isProtectionActive ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                _audioService.isProtectionActive ? 'VOXSHIELD PROTECTED' : 'CALL ACTIVE',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
            ],
          ),
          IconButton(
            icon: Icon(
              _isOverlayMinimized ? Icons.visibility_off_rounded : Icons.visibility_rounded,
              color: Colors.white70,
              size: 20,
            ),
            onPressed: () {
              setState(() {
                _isOverlayMinimized = !_isOverlayMinimized;
                if (_isOverlayMinimized) {
                  _slideController.reverse();
                } else {
                  _slideController.forward();
                }
              });
            },
            tooltip: 'Toggle Detection Notification',
          ),
        ],
      ),
    );
  }

  Widget _buildCallerProfile() {
    return Column(
      children: [
        Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF1E293B),
                border: Border.all(
                  color: _audioService.isProtectionActive
                      ? (_liveAnalysis?.level.color ?? const Color(0xFFF97316))
                      : const Color(0xFF475569),
                  width: 2.5,
                ),
              ),
              child: const Icon(
                Icons.person_rounded,
                size: 46,
                color: Colors.white70,
              ),
            ),
            if (!_isAnswered)
              Positioned(
                bottom: 0,
                right: 0,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: const BoxDecoration(
                    color: Color(0xFF10B981),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.phone_in_talk, size: 14, color: Colors.white),
                ),
              ),
          ],
        ),
        const SizedBox(height: 10),
        Text(
          widget.callerName,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.3,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 2),
        Text(
          widget.callerNumber,
          style: const TextStyle(
            color: Colors.white60,
            fontSize: 13,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
          decoration: BoxDecoration(
            color: const Color(0xFF1E293B),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            _isAnswered ? _formatDuration(_secondsElapsed) : 'Incoming VoIP Call...',
            style: TextStyle(
              color: _isAnswered ? const Color(0xFF38BDF8) : Colors.amberAccent,
              fontSize: 11,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }

  /// Slide-In Notification Menu matching the exact user UI specification
  Widget _buildSlideInMenu() {
    return SlideTransition(
      position: _slideAnimation,
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: _audioService.isProtectionActive
                ? const Color(0xFFF97316)
                : const Color(0xFF475569),
            width: 1.8,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.5),
              blurRadius: 18,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: _audioService.isProtectionActive
            ? _buildProtectedStateExact()
            : _buildUnprotectedStateExact(),
      ),
    );
  }

  /// ┌─────────────────────────────┐
  /// │       VOICEGUARD            │
  /// │                             │
  /// │   📞 CALL ACTIVE             │
  /// │                             │
  /// │   Protection: OFF           │
  /// │                             │
  /// │  ┌───────────────────────┐  │
  /// │  │ TURN ON PROTECTION    │  │
  /// │  └───────────────────────┘  │
  /// │                             │
  /// └─────────────────────────────┘
  Widget _buildUnprotectedStateExact() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // VOICEGUARD Title
        const Text(
          'VOICEGUARD',
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w900,
            letterSpacing: 2.5,
          ),
        ),
        const SizedBox(height: 20),

        // 📞 CALL ACTIVE
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.phone_in_talk_rounded, color: Color(0xFF10B981), size: 22),
            const SizedBox(width: 8),
            Text(
              _isAnswered ? 'CALL ACTIVE' : 'INCOMING CALL',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Protection: OFF
        const Text(
          'Protection: OFF',
          style: TextStyle(
            color: Colors.white70,
            fontSize: 14,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.8,
          ),
        ),
        const SizedBox(height: 22),

        // [ TURN ON PROTECTION ] Button
        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFF60A5FA), width: 1.5),
          ),
          child: ElevatedButton(
            onPressed: _activateProtection,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF1E3A8A),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(7),
              ),
            ),
            child: const Text(
              'TURN ON PROTECTION',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.5,
              ),
            ),
          ),
        ),
      ],
    );
  }

  /// ┌─────────────────────────────┐
  /// │       🛡 PROTECTED          │
  /// │                             │
  /// │       RISK SCORE            │
  /// │          72                 │
  /// │       ORANGE ⚠️             │
  /// │                             │
  /// │ Deepfake       78%          │
  /// │ Scam           81%          │
  /// │ Urgency        70%          │
  /// │                             │
  /// │ ⚠️ OTP request detected     │
  /// │ ⚠️ Urgent payment request   │
  /// │                             │
  /// │ [ STOP PROTECTION ]         │
  /// └─────────────────────────────┘
  Widget _buildProtectedStateExact() {
    final analysis = _liveAnalysis ??
        CallAnalysis(
          overallRisk: 72,
          level: RiskLevel.high,
          voiceRisk: 78,
          scamRisk: 81,
          urgencyScore: 70,
          voiceAnalysis: VoiceAnalysisResult(isAiVoice: true, confidence: 0.78),
          transcript: '',
          warnings: [
            ScamWarning(
              id: 'w1',
              title: '⚠️ OTP request detected',
              description: 'Caller demanded 6-digit SMS verification code',
              category: 'OTP',
              severity: RiskLevel.critical,
            ),
            ScamWarning(
              id: 'w2',
              title: '⚠️ Urgent payment request',
              description: 'Immediate financial authorization pressure detected',
              category: 'URGENT_PAYMENT',
              severity: RiskLevel.high,
            ),
          ],
          detectedPatterns: ['OTP Harvesting', 'Deepfake Neural Voice'],
        );

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // 🛡 PROTECTED
        const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.shield_rounded, color: Color(0xFF10B981), size: 20),
            SizedBox(width: 8),
            Text(
              'PROTECTED',
              style: TextStyle(
                color: Color(0xFF10B981),
                fontSize: 16,
                fontWeight: FontWeight.w900,
                letterSpacing: 2.0,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // RISK SCORE
        const Text(
          'RISK SCORE',
          style: TextStyle(
            color: Colors.white70,
            fontSize: 13,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.5,
          ),
        ),
        const SizedBox(height: 4),

        // 72
        Text(
          '${analysis.overallRisk}',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 44,
            fontWeight: FontWeight.w900,
            height: 1.0,
          ),
        ),
        const SizedBox(height: 6),

        // ORANGE ⚠️ Badge
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            color: analysis.level.color.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: analysis.level.color.withValues(alpha: 0.8), width: 1.2),
          ),
          child: Text(
            analysis.level.colorBadgeText,
            style: TextStyle(
              color: analysis.level.color,
              fontSize: 12,
              fontWeight: FontWeight.w900,
              letterSpacing: 1.0,
            ),
          ),
        ),
        const SizedBox(height: 18),

        // Metrics Breakdown:
        // Deepfake       78%
        // Scam           81%
        // Urgency        70%
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: const Color(0xFF1E293B).withValues(alpha: 0.6),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF334155)),
          ),
          child: Column(
            children: [
              _buildMetricTextRow('Deepfake', '${analysis.voiceRisk}%', const Color(0xFFEF4444)),
              const SizedBox(height: 6),
              _buildMetricTextRow('Scam', '${analysis.scamRisk}%', const Color(0xFFF97316)),
              const SizedBox(height: 6),
              _buildMetricTextRow('Urgency', '${analysis.urgencyScore}%', const Color(0xFFFBBF24)),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // ⚠️ OTP request detected
        // ⚠️ Urgent payment request
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildWarningItem('⚠️ OTP request detected', const Color(0xFFEF4444)),
            const SizedBox(height: 6),
            _buildWarningItem('⚠️ Urgent payment request', const Color(0xFFF97316)),
          ],
        ),
        const SizedBox(height: 18),

        // [ STOP PROTECTION ] Button
        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFFEF4444), width: 1.2),
          ),
          child: TextButton(
            onPressed: _stopProtection,
            style: TextButton.styleFrom(
              foregroundColor: const Color(0xFFEF4444),
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(7),
              ),
            ),
            child: const Text(
              '[ STOP PROTECTION ]',
              style: TextStyle(
                fontWeight: FontWeight.w900,
                fontSize: 13,
                letterSpacing: 1.2,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMetricTextRow(String label, String value, Color valueColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            color: valueColor,
            fontSize: 13,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }

  Widget _buildWarningItem(String text, Color color) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _buildOverlayDisabledNotice() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: Colors.white70, size: 18),
          const SizedBox(width: 8),
          const Expanded(
            child: Text(
              'Notification overlay hidden per user settings.',
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
          ),
          TextButton(
            onPressed: () {
              setState(() {
                widget.settings.isOverlayEnabled = true;
                _slideController.forward();
              });
            },
            child: const Text('Show Notification'),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveTranscriptBox() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B).withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF334155)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.subtitles_outlined, size: 14, color: Color(0xFF38BDF8)),
              SizedBox(width: 6),
              Text(
                'LIVE SPEECH TRANSCRIPT',
                style: TextStyle(
                  color: Color(0xFF38BDF8),
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.0,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            _liveTranscript.isNotEmpty
                ? _liveTranscript
                : 'Listening to incoming call audio stream for conversational cues...',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12.5,
              height: 1.35,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCallControls() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_isAnswered) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildToolButton(
                  icon: _isMuted ? Icons.mic_off_rounded : Icons.mic_rounded,
                  label: _isMuted ? 'Unmute' : 'Mute',
                  isActive: _isMuted,
                  onTap: () {
                    setState(() => _isMuted = !_isMuted);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(_isMuted ? '🔇 Microphone muted.' : '🎙️ Microphone live.'),
                        duration: const Duration(milliseconds: 1200),
                        backgroundColor: const Color(0xFF1E293B),
                      ),
                    );
                  },
                ),
                _buildToolButton(
                  icon: Icons.dialpad_rounded,
                  label: 'Keypad',
                  isActive: false,
                  onTap: _openKeypadModal,
                ),
                _buildToolButton(
                  icon: _isSpeaker ? Icons.volume_up_rounded : Icons.volume_down_rounded,
                  label: 'Speaker',
                  isActive: _isSpeaker,
                  onTap: () {
                    setState(() => _isSpeaker = !_isSpeaker);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(_isSpeaker ? '🔊 Speakerphone ON.' : '📱 Earpiece mode.'),
                        duration: const Duration(milliseconds: 1200),
                        backgroundColor: const Color(0xFF1E293B),
                      ),
                    );
                  },
                ),
                _buildToolButton(
                  icon: _audioService.isProtectionActive
                      ? Icons.shield_rounded
                      : Icons.shield_outlined,
                  label: _audioService.isProtectionActive ? 'Protected' : 'Protect',
                  isActive: _audioService.isProtectionActive,
                  activeColor: const Color(0xFF10B981),
                  onTap: () {
                    if (_audioService.isProtectionActive) {
                      _stopProtection();
                    } else {
                      _activateProtection();
                    }
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
          ],

          // Bottom Action Buttons (Answer / Decline / End Call)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              if (!_isAnswered) ...[
                _buildBigActionButton(
                  color: const Color(0xFFEF4444),
                  icon: Icons.call_end_rounded,
                  label: 'Decline',
                  onTap: () => Navigator.pop(context),
                ),
                _buildBigActionButton(
                  color: const Color(0xFF10B981),
                  icon: Icons.call_rounded,
                  label: 'Answer',
                  onTap: _answerCall,
                ),
              ] else ...[
                _buildBigActionButton(
                  color: const Color(0xFFEF4444),
                  icon: Icons.call_end_rounded,
                  label: 'End Call & View Report',
                  isWide: true,
                  onTap: _endCall,
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildToolButton({
    required IconData icon,
    required String label,
    required bool isActive,
    Color? activeColor,
    required VoidCallback onTap,
  }) {
    final effectiveActiveColor = activeColor ?? const Color(0xFF38BDF8);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isActive ? effectiveActiveColor.withValues(alpha: 0.2) : const Color(0xFF1E293B),
                border: Border.all(
                  color: isActive ? effectiveActiveColor : const Color(0xFF334155),
                ),
              ),
              child: Icon(
                icon,
                color: isActive ? effectiveActiveColor : Colors.white70,
                size: 22,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isActive ? effectiveActiveColor : Colors.white60,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBigActionButton({
    required Color color,
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool isWide = false,
  }) {
    if (isWide) {
      return Expanded(
        child: ElevatedButton.icon(
          onPressed: onTap,
          icon: Icon(icon, color: Colors.white, size: 22),
          label: Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 15,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.5,
            ),
          ),
          style: ElevatedButton.styleFrom(
            backgroundColor: color,
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            elevation: 4,
          ),
        ),
      );
    }

    return Column(
      children: [
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: color.withValues(alpha: 0.4),
                  blurRadius: 12,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Icon(icon, color: Colors.white, size: 28),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
