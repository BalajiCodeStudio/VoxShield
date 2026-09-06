import 'dart:async';
import 'package:flutter/material.dart';
import '../models/call_analysis.dart';
import '../services/audio_service.dart';
import '../widgets/analysis_card.dart';
import '../widgets/risk_meter.dart';
import '../widgets/voice_status.dart';
import '../widgets/warning_card.dart';
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
  bool _showKeypad = false;
  bool _isOverlayMinimized = false;

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
      duration: const Duration(milliseconds: 600),
    );

    // Slide in from left/right
    _slideAnimation = Tween<Offset>(
      begin: const Offset(-1.2, 0.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeOutBack,
    ));

    _audioService.startIncomingCall(
      callerName: widget.callerName,
      callerNumber: widget.callerNumber,
      scenario: widget.scenario,
    );

    // If auto protect is turned on in settings, auto answer after a delay or auto activate
    if (widget.settings.autoProtectOnCall) {
      Future.delayed(const Duration(milliseconds: 800), () {
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

    // Automatically slide HUD menu into screen upon call arrival/answer
    if (widget.settings.isOverlayEnabled) {
      Future.delayed(const Duration(milliseconds: 300), () {
        if (mounted) {
          _slideController.forward();
        }
      });
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
    _audioService.turnOnProtection();
    setState(() {});
  }

  void _stopProtection() {
    _audioService.stopProtection();
    setState(() {});
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
            // Background ambient lighting
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

            // Main Call User Interface
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

                        // If call is answered and overlay is enabled, show the animated HUD Menu
                        if (_isAnswered && widget.settings.isOverlayEnabled)
                          _buildSlideInMenu(),

                        // If overlay is disabled in settings, show a clean indicator
                        if (_isAnswered && !widget.settings.isOverlayEnabled)
                          _buildOverlayDisabledNotice(),

                        const SizedBox(height: 16),

                        // Real-time live transcript feed if enabled and protection is on
                        if (_isAnswered && _audioService.isProtectionActive && widget.settings.showLiveTranscript)
                          _buildLiveTranscriptBox(),

                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),

                // Call action buttons (Keypad, Mute, Speaker, Answer / End)
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
                  color: _isAnswered ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                _isAnswered ? 'VOXSHIELD SHIELD ACTIVE' : 'INCOMING CALL DETECTED',
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
            tooltip: 'Toggle Detection HUD',
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
              width: 88,
              height: 88,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF1E293B),
                border: Border.all(
                  color: _audioService.isProtectionActive
                      ? (_liveAnalysis?.level.color ?? const Color(0xFF38BDF8))
                      : const Color(0xFF475569),
                  width: 2.5,
                ),
              ),
              child: const Icon(
                Icons.person_rounded,
                size: 50,
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
                  child: const Icon(Icons.phone_in_talk, size: 16, color: Colors.white),
                ),
              ),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          widget.callerName,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.3,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 4),
        Text(
          widget.callerNumber,
          style: const TextStyle(
            color: Colors.white60,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: const Color(0xFF1E293B),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            _isAnswered ? _formatDuration(_secondsElapsed) : 'Incoming VoIP Call...',
            style: TextStyle(
              color: _isAnswered ? const Color(0xFF38BDF8) : Colors.amberAccent,
              fontSize: 12,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }

  /// The requested Slide-In HUD Menu with Before / After Activation States
  Widget _buildSlideInMenu() {
    return SlideTransition(
      position: _slideAnimation,
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF131B2E).withValues(alpha: 0.96),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: _audioService.isProtectionActive
                ? (_liveAnalysis?.level.color.withValues(alpha: 0.6) ?? const Color(0xFF06B6D4))
                : const Color(0xFF334155),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.45),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: _audioService.isProtectionActive
            ? _buildProtectedHUDState()
            : _buildUnprotectedHUDState(),
      ),
    );
  }

  /// State BEFORE Activation
  Widget _buildUnprotectedHUDState() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text(
                'VOICEGUARD / VOXSHIELD',
                style: TextStyle(
                  color: Color(0xFF38BDF8),
                  fontSize: 13,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.5,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.phone_in_talk_rounded, color: Color(0xFF10B981), size: 20),
            SizedBox(width: 8),
            Text(
              'CALL ACTIVE',
              style: TextStyle(
                color: Colors.white,
                fontSize: 15,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.0,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
          decoration: BoxDecoration(
            color: const Color(0xFFEF4444).withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Text(
            'Protection: OFF',
            style: TextStyle(
              color: Color(0xFFF87171),
              fontSize: 12,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        const SizedBox(height: 16),

        // TURN ON PROTECTION Button
        SizedBox(
          width: double.infinity,
          height: 48,
          child: ElevatedButton(
            onPressed: _activateProtection,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF2563EB),
              foregroundColor: Colors.white,
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: const BorderSide(color: Color(0xFF60A5FA), width: 1.2),
              ),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.shield_outlined, size: 20),
                SizedBox(width: 8),
                Text(
                  'TURN ON PROTECTION',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.1,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// State AFTER Activation
  Widget _buildProtectedHUDState() {
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
              description: 'Caller demanded 6-digit passcode',
              category: 'OTP',
              severity: RiskLevel.critical,
            ),
            ScamWarning(
              id: 'w2',
              title: '⚠️ Urgent payment request',
              description: 'High-pressure financial demand detected',
              category: 'URGENT_PAYMENT',
              severity: RiskLevel.high,
            ),
          ],
          detectedPatterns: ['OTP Theft', 'Deepfake Neural Voice'],
        );

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Header: 🛡 PROTECTED
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Row(
              children: [
                Icon(Icons.verified_user_rounded, color: Color(0xFF10B981), size: 18),
                SizedBox(width: 6),
                Text(
                  '🛡 PROTECTED',
                  style: TextStyle(
                    color: Color(0xFF10B981),
                    fontSize: 14,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1.2,
                  ),
                ),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: const Color(0xFFEF4444).withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                'LIVE MONITORING',
                style: TextStyle(
                  color: Color(0xFFF87171),
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),

        // Live Risk Meter (Displays Score e.g. 72, Level badge e.g. ORANGE ⚠️)
        RiskMeter(
          score: analysis.overallRisk,
          level: analysis.level,
          size: 140,
        ),
        const SizedBox(height: 14),

        // Deepfake, Scam, Urgency metrics breakdown
        AnalysisCard(
          deepfakeScore: analysis.voiceRisk,
          scamScore: analysis.scamRisk,
          urgencyScore: analysis.urgencyScore,
          isCompact: true,
        ),
        const SizedBox(height: 12),

        // Voice Biometrics and Waveform Status
        VoiceStatusWidget(
          voiceAnalysis: analysis.voiceAnalysis,
          waveformStream: _audioService.waveformStream,
          isLive: true,
        ),
        const SizedBox(height: 12),

        // Detected Scam Warnings List (e.g. ⚠️ OTP request detected, ⚠️ Urgent payment request)
        if (analysis.warnings.isNotEmpty) ...[
          Column(
            children: analysis.warnings
                .map((w) => WarningCard(warning: w, isCompact: true))
                .toList(),
          ),
          const SizedBox(height: 12),
        ],

        // STOP PROTECTION button
        SizedBox(
          width: double.infinity,
          height: 42,
          child: OutlinedButton(
            onPressed: _stopProtection,
            style: OutlinedButton.styleFrom(
              foregroundColor: const Color(0xFFEF4444),
              side: const BorderSide(color: Color(0xFFEF4444), width: 1.2),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.stop_circle_outlined, size: 18),
                SizedBox(width: 6),
                Text(
                  'STOP PROTECTION',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 13,
                    letterSpacing: 1.0,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
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
              'HUD overlay hidden per user settings. Background monitoring active.',
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
            child: const Text('Show HUD'),
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
            // Middle in-call tools: Mute, Keypad, Speaker, Shield Toggle
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildToolButton(
                  icon: _isMuted ? Icons.mic_off_rounded : Icons.mic_rounded,
                  label: _isMuted ? 'Unmute' : 'Mute',
                  isActive: _isMuted,
                  onTap: () => setState(() => _isMuted = !_isMuted),
                ),
                _buildToolButton(
                  icon: Icons.dialpad_rounded,
                  label: 'Keypad',
                  isActive: _showKeypad,
                  onTap: () => setState(() => _showKeypad = !_showKeypad),
                ),
                _buildToolButton(
                  icon: _isSpeaker ? Icons.volume_up_rounded : Icons.volume_down_rounded,
                  label: 'Speaker',
                  isActive: _isSpeaker,
                  onTap: () => setState(() => _isSpeaker = !_isSpeaker),
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

          // Big Bottom Action Buttons (Accept / End Call)
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              if (!_isAnswered) ...[
                // Decline Button
                _buildBigActionButton(
                  color: const Color(0xFFEF4444),
                  icon: Icons.call_end_rounded,
                  label: 'Decline',
                  onTap: () => Navigator.pop(context),
                ),
                // Answer Button
                _buildBigActionButton(
                  color: const Color(0xFF10B981),
                  icon: Icons.call_rounded,
                  label: 'Answer',
                  onTap: _answerCall,
                ),
              ] else ...[
                // End Call Button
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
