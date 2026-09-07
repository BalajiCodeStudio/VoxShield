import 'package:flutter/material.dart';
import '../models/call_analysis.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import '../services/call_monitor.dart';
import 'call_screen.dart';
import 'history_screen.dart';
import 'risk_screen.dart';

class HomeScreen extends StatefulWidget {
  final AppSettings settings;

  const HomeScreen({
    super.key,
    required this.settings,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final AudioStreamService _audioService = AudioStreamService();
  final ApiService _apiService = ApiService();
  bool _isShieldEnabled = true;
  bool _isBackendOnline = false;
  String _pingLatency = '';
  bool _phonePermission = false;
  bool _micPermission = false;
  bool _overlayPermission = false;

  @override
  void initState() {
    super.initState();
    _audioService.initializeDemoHistory();
    _checkServer();
    _checkPermissions();
  }

  void _checkPermissions() async {
    final status = await CallMonitorService().checkPermissions();
    if (mounted) {
      setState(() {
        _phonePermission = status['phone'] ?? false;
        _micPermission = status['mic'] ?? false;
        _overlayPermission = status['overlay'] ?? false;
      });
    }
  }

  void _requestAllPermissions() async {
    await CallMonitorService().requestAllPermissions();
    _checkPermissions();
  }

  void _checkServer() async {
    final stopwatch = Stopwatch()..start();
    final online = await _apiService.checkHealth();
    stopwatch.stop();

    if (mounted) {
      setState(() {
        _isBackendOnline = online;
        _pingLatency = online ? '${stopwatch.elapsedMilliseconds}ms' : 'Offline';
      });
    }
  }

  void _launchCallSimulation({
    required String name,
    required String number,
    required String scenario,
  }) {
    if (!_isShieldEnabled) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('⚠️ Master Shield is paused. Enabling shield for test call.'),
          backgroundColor: Color(0xFFF59E0B),
          duration: Duration(seconds: 2),
        ),
      );
      setState(() => _isShieldEnabled = true);
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => CallScreen(
          callerName: name,
          callerNumber: number,
          scenario: scenario,
          settings: widget.settings,
        ),
      ),
    ).then((_) => setState(() {}));
  }

  void _openCustomCallSimulatorDialog() {
    final nameCtrl = TextEditingController(text: 'Unknown Suspicious Caller');
    final phoneCtrl = TextEditingController(text: '+1 (888) 555-0199');
    String selectedScenario = 'bank_otp_scam';

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: const Color(0xFF0F172A),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: const BorderSide(color: Color(0xFF334155)),
              ),
              title: const Row(
                children: [
                  Icon(Icons.tune_rounded, color: Color(0xFF38BDF8)),
                  SizedBox(width: 8),
                  Text('Custom Test Call', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('CALLER NAME', style: TextStyle(color: Colors.white60, fontSize: 11, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    TextField(
                      controller: nameCtrl,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        filled: true,
                        fillColor: const Color(0xFF1E293B),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Text('PHONE NUMBER', style: TextStyle(color: Colors.white60, fontSize: 11, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    TextField(
                      controller: phoneCtrl,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        filled: true,
                        fillColor: const Color(0xFF1E293B),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                      ),
                    ),
                    const SizedBox(height: 14),
                    const Text('THREAT SCENARIO', style: TextStyle(color: Colors.white60, fontSize: 11, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      initialValue: selectedScenario,
                      dropdownColor: const Color(0xFF1E293B),
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        filled: true,
                        fillColor: const Color(0xFF1E293B),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'bank_otp_scam', child: Text('🏦 Bank OTP Scam (Score 72 - Orange)')),
                        DropdownMenuItem(value: 'family_emergency_deepfake', child: Text('🚨 Deepfake Voice Extortion (Score 89 - Red)')),
                        DropdownMenuItem(value: 'legitimate_call', child: Text('✅ Safe Contact Call (Score 12 - Green)')),
                      ],
                      onChanged: (val) {
                        if (val != null) setDialogState(() => selectedScenario = val);
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel', style: TextStyle(color: Colors.white60)),
                ),
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    _launchCallSimulation(
                      name: nameCtrl.text.trim().isEmpty ? 'Unknown Caller' : nameCtrl.text.trim(),
                      number: phoneCtrl.text.trim().isEmpty ? '+1 (800) 000-0000' : phoneCtrl.text.trim(),
                      scenario: selectedScenario,
                    );
                  },
                  icon: const Icon(Icons.phone_in_talk, size: 16),
                  label: const Text('Start Call'),
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2563EB)),
                ),
              ],
            );
          },
        );
      },
    );
  }

  void _openSettingsDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF0F172A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                top: 20,
                left: 20,
                right: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 44,
                        height: 4,
                        decoration: BoxDecoration(
                          color: const Color(0xFF334155),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Row(
                      children: [
                        Icon(Icons.settings_suggest_rounded, color: Color(0xFF38BDF8), size: 24),
                        SizedBox(width: 8),
                        Text(
                          'Protection & Overlay Settings',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 18),

                    // HUD Slide-in Overlay Switch
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E293B),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFF334155)),
                      ),
                      child: Column(
                        children: [
                          SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: const Text(
                              'Slide-In Detection HUD',
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
                            ),
                            subtitle: const Text(
                              'Automatically slide HUD into active calls. Disable to completely hide notifications during calls.',
                              style: TextStyle(color: Colors.white60, fontSize: 12),
                            ),
                            value: widget.settings.isOverlayEnabled,
                            activeThumbColor: const Color(0xFF10B981),
                            onChanged: (val) {
                              setModalState(() => widget.settings.isOverlayEnabled = val);
                              setState(() {});
                            },
                          ),
                          const Divider(color: Color(0xFF334155), height: 16),
                          SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: const Text(
                              'Auto-Protect on Answer',
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
                            ),
                            subtitle: const Text(
                              'Instantly activate real-time AI scanning when call is answered.',
                              style: TextStyle(color: Colors.white60, fontSize: 12),
                            ),
                            value: widget.settings.autoProtectOnCall,
                            activeThumbColor: const Color(0xFF38BDF8),
                            onChanged: (val) {
                              setModalState(() => widget.settings.autoProtectOnCall = val);
                              setState(() {});
                            },
                          ),
                          const Divider(color: Color(0xFF334155), height: 16),
                          SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: const Text(
                              'Live Speech Transcript',
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
                            ),
                            subtitle: const Text(
                              'Display streaming transcript box under active call.',
                              style: TextStyle(color: Colors.white60, fontSize: 12),
                            ),
                            value: widget.settings.showLiveTranscript,
                            activeThumbColor: const Color(0xFF38BDF8),
                            onChanged: (val) {
                              setModalState(() => widget.settings.showLiveTranscript = val);
                              setState(() {});
                            },
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Sensitivity slider
                    const Text(
                      'DETECTION SENSITIVITY',
                      style: TextStyle(
                        color: Colors.white60,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.1,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Slider(
                      value: widget.settings.sensitivityThreshold.toDouble(),
                      min: 30,
                      max: 95,
                      divisions: 13,
                      label: '${widget.settings.sensitivityThreshold}%',
                      activeColor: const Color(0xFF38BDF8),
                      inactiveColor: const Color(0xFF1E293B),
                      onChanged: (val) {
                        setModalState(() => widget.settings.sensitivityThreshold = val.round());
                        setState(() {});
                      },
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Strict (High Alerts)', style: TextStyle(color: Colors.white38, fontSize: 11)),
                        Text('${widget.settings.sensitivityThreshold}% Standard', style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 12, fontWeight: FontWeight.bold)),
                        const Text('Relaxed', style: TextStyle(color: Colors.white38, fontSize: 11)),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Backend API Endpoint input
                    const Text(
                      'BACKEND API SERVER',
                      style: TextStyle(
                        color: Colors.white60,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.1,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      initialValue: widget.settings.backendUrl,
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                      decoration: InputDecoration(
                        filled: true,
                        fillColor: const Color(0xFF1E293B),
                        hintText: 'http://127.0.0.1:8000',
                        hintStyle: const TextStyle(color: Colors.white38),
                        prefixIcon: Icon(
                          _isBackendOnline ? Icons.cloud_done_rounded : Icons.cloud_off_rounded,
                          color: _isBackendOnline ? const Color(0xFF10B981) : Colors.orangeAccent,
                          size: 20,
                        ),
                        suffixIcon: TextButton(
                          onPressed: () async {
                            final sw = Stopwatch()..start();
                            final res = await _apiService.checkHealth();
                            sw.stop();
                            setModalState(() {
                              _isBackendOnline = res;
                              _pingLatency = res ? '${sw.elapsedMilliseconds}ms' : 'Offline';
                            });
                            setState(() {});
                          },
                          child: Text(_pingLatency.isNotEmpty ? _pingLatency : 'Test', style: const TextStyle(color: Color(0xFF38BDF8))),
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      onChanged: (val) {
                        widget.settings.backendUrl = val;
                        _apiService.updateBaseUrl(val);
                      },
                    ),
                    const SizedBox(height: 20),

                    // Close Button
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: ElevatedButton(
                        onPressed: () => Navigator.pop(context),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF2563EB),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: const Text(
                          'Save Settings',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                            fontSize: 14,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1D),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF2563EB).withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.shield_rounded, color: Color(0xFF38BDF8), size: 22),
            ),
            const SizedBox(width: 10),
            const Text(
              'VoxShield',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w900,
                fontSize: 20,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.history_rounded, color: Colors.white70),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const HistoryScreen()),
              ).then((_) => setState(() {}));
            },
            tooltip: 'Call History',
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: Colors.white70),
            onPressed: _openSettingsDialog,
            tooltip: 'Settings',
          ),
        ],
      ),
      body: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Active Shield Master Banner
            _buildMasterShieldCard(),
            const SizedBox(height: 16),

            // Live Call Overlay & Phone Call Protection Banner
            _buildLiveCallProtectionCard(),
            const SizedBox(height: 20),

            // Statistics Grid
            _buildStatsGrid(),
            const SizedBox(height: 24),

            // Simulation Test Suite
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'TEST CALL SIMULATION',
                  style: TextStyle(
                    color: Colors.white60,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.2,
                  ),
                ),
                InkWell(
                  onTap: _openCustomCallSimulatorDialog,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF38BDF8).withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFF38BDF8).withValues(alpha: 0.4)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.add_call, size: 12, color: Color(0xFF38BDF8)),
                        SizedBox(width: 4),
                        Text(
                          'CUSTOM CALL',
                          style: TextStyle(
                            color: Color(0xFF38BDF8),
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            _buildSimulationCard(
              title: 'Bank OTP Impersonator',
              subtitle: 'Chase Security asking for 6-digit SMS passcode with cloned audio',
              phone: '+1 (800) 935-9935',
              riskScore: 72,
              riskBadge: 'ORANGE ⚠️',
              riskColor: const Color(0xFFF97316),
              icon: Icons.account_balance_rounded,
              onTap: () => _launchCallSimulation(
                name: 'Chase Fraud Security (Spoofed)',
                number: '+1 (800) 935-9935',
                scenario: 'bank_otp_scam',
              ),
            ),
            const SizedBox(height: 10),
            _buildSimulationCard(
              title: 'Family Emergency Deepfake',
              subtitle: 'Zero-shot AI voice clone requesting urgent wire transfer',
              phone: '+1 (415) 890-1122',
              riskScore: 89,
              riskBadge: 'RED 🚨',
              riskColor: const Color(0xFFEF4444),
              icon: Icons.record_voice_over_rounded,
              onTap: () => _launchCallSimulation(
                name: 'Unknown Family Distress Call',
                number: '+1 (415) 890-1122',
                scenario: 'family_emergency_deepfake',
              ),
            ),
            const SizedBox(height: 10),
            _buildSimulationCard(
              title: 'Verified Safe Contact',
              subtitle: 'Natural speech, genuine conversation without social engineering',
              phone: '+1 (555) 234-5678',
              riskScore: 12,
              riskBadge: 'GREEN 🛡️',
              riskColor: const Color(0xFF10B981),
              icon: Icons.person_pin_rounded,
              onTap: () => _launchCallSimulation(
                name: 'Alex Morgan',
                number: '+1 (555) 234-5678',
                scenario: 'legitimate_call',
              ),
            ),
            const SizedBox(height: 24),

            // Recent Scans Quick Access
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'RECENT CALL SCANS',
                  style: TextStyle(
                    color: Colors.white60,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.2,
                  ),
                ),
                TextButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => const HistoryScreen()),
                    ).then((_) => setState(() {}));
                  },
                  child: const Text('View All', style: TextStyle(color: Color(0xFF38BDF8), fontSize: 12)),
                ),
              ],
            ),
            _buildRecentScansSnippet(),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildMasterShieldCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1E3A8A), Color(0xFF0F172A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: _isShieldEnabled ? const Color(0xFF38BDF8).withValues(alpha: 0.5) : const Color(0xFF334155),
          width: 1.5,
        ),
        boxShadow: [
          if (_isShieldEnabled)
            BoxShadow(
              color: const Color(0xFF38BDF8).withValues(alpha: 0.15),
              blurRadius: 18,
              spreadRadius: 2,
            ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _isShieldEnabled ? const Color(0xFF10B981).withValues(alpha: 0.2) : const Color(0xFF334155),
            ),
            child: Icon(
              _isShieldEnabled ? Icons.verified_user_rounded : Icons.shield_outlined,
              color: _isShieldEnabled ? const Color(0xFF10B981) : Colors.white60,
              size: 32,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _isShieldEnabled ? 'Real-Time Protection ON' : 'Protection Paused',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _isShieldEnabled
                      ? 'HUD will slide in automatically when call arrives.'
                      : 'Incoming calls will not be analyzed.',
                  style: const TextStyle(color: Colors.white70, fontSize: 12),
                ),
              ],
            ),
          ),
          Switch(
            value: _isShieldEnabled,
            activeThumbColor: const Color(0xFF10B981),
            onChanged: (val) {
              setState(() {
                _isShieldEnabled = val;
              });
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(val ? '🛡️ Master Protection Enabled.' : '⏸️ Master Protection Paused.'),
                  duration: const Duration(seconds: 1),
                  backgroundColor: const Color(0xFF1E293B),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildLiveCallProtectionCard() {
    final allGranted = _phonePermission && _micPermission && _overlayPermission;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF131B2E),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: allGranted ? const Color(0xFF10B981).withValues(alpha: 0.4) : const Color(0xFFF59E0B).withValues(alpha: 0.4),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                allGranted ? Icons.check_circle_rounded : Icons.warning_amber_rounded,
                color: allGranted ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                size: 20,
              ),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Live Call Slide-In Protection',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 14),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Requires 3 permissions to detect calls, analyze speakerphone audio, and slide the HUD over your dialer.',
            style: TextStyle(color: Colors.white70, fontSize: 12),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              _buildPermissionBadge('Overlay', _overlayPermission),
              _buildPermissionBadge('Phone', _phonePermission),
              _buildPermissionBadge('Microphone', _micPermission),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              if (!allGranted)
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _requestAllPermissions,
                    icon: const Icon(Icons.security, size: 16),
                    label: const Text('Grant All', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF2563EB),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ),
              if (!allGranted) const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () async {
                    if (!_overlayPermission) {
                      await CallMonitorService().requestAllPermissions();
                      _checkPermissions();
                    }
                    await CallMonitorService().testTriggerOverlay();
                  },
                  icon: const Icon(Icons.smart_display_outlined, size: 16, color: Color(0xFF38BDF8)),
                  label: const Text('Test HUD', style: TextStyle(color: Color(0xFF38BDF8), fontSize: 12, fontWeight: FontWeight.bold)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Color(0xFF38BDF8)),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPermissionBadge(String label, bool isGranted) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isGranted ? const Color(0xFF10B981).withValues(alpha: 0.15) : const Color(0xFFEF4444).withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: isGranted ? const Color(0xFF10B981).withValues(alpha: 0.5) : const Color(0xFFEF4444).withValues(alpha: 0.5),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isGranted ? Icons.check : Icons.close,
            size: 12,
            color: isGranted ? const Color(0xFF10B981) : const Color(0xFFEF4444),
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              color: isGranted ? const Color(0xFF10B981) : const Color(0xFFEF4444),
              fontSize: 11,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid() {
    return Row(
      children: [
        Expanded(
          child: _buildStatTile(
            title: 'Scanned',
            value: '${_audioService.totalScannedCount}',
            icon: Icons.phone_callback_rounded,
            color: const Color(0xFF38BDF8),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildStatTile(
            title: 'Blocked',
            value: '${_audioService.totalBlockedCount}',
            icon: Icons.gpp_bad_rounded,
            color: const Color(0xFFEF4444),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildStatTile(
            title: 'Deepfakes',
            value: '${_audioService.totalDeepfakesCount}',
            icon: Icons.record_voice_over_rounded,
            color: const Color(0xFFF97316),
          ),
        ),
      ],
    );
  }

  Widget _buildStatTile({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF131B2E),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            title,
            style: const TextStyle(
              color: Colors.white60,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSimulationCard({
    required String title,
    required String subtitle,
    required String phone,
    required int riskScore,
    required String riskBadge,
    required Color riskColor,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF131B2E),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: riskColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(icon, color: riskColor, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              title,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w800,
                                fontSize: 14,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: riskColor.withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              riskBadge,
                              style: TextStyle(
                                color: riskColor,
                                fontWeight: FontWeight.w800,
                                fontSize: 10,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        subtitle,
                        style: const TextStyle(color: Colors.white60, fontSize: 12),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      const Row(
                        children: [
                          Icon(Icons.play_circle_fill_rounded, size: 14, color: Color(0xFF38BDF8)),
                          SizedBox(width: 4),
                          Text(
                            'Simulate Incoming Call',
                            style: TextStyle(
                              color: Color(0xFF38BDF8),
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRecentScansSnippet() {
    final recent = _audioService.callHistory.take(2).toList();
    if (recent.isEmpty) {
      return const SizedBox();
    }

    return Column(
      children: recent.map((r) {
        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          decoration: BoxDecoration(
            color: const Color(0xFF131B2E),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFF1E293B)),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => RiskScreen(analysis: r.analysis),
                  ),
                );
              },
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(r.level.icon, color: r.level.color, size: 20),
                        const SizedBox(width: 10),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              r.callerName,
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13),
                            ),
                            Text(
                              r.callerNumber,
                              style: const TextStyle(color: Colors.white60, fontSize: 11),
                            ),
                          ],
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: r.level.color.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '${r.overallRisk}% Risk',
                        style: TextStyle(color: r.level.color, fontWeight: FontWeight.bold, fontSize: 11),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
