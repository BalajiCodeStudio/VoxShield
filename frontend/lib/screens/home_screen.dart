import 'package:flutter/material.dart';
import '../models/call_analysis.dart';
import '../services/api_service.dart';
import '../services/audio_service.dart';
import 'call_screen.dart';
import 'history_screen.dart';

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

  @override
  void initState() {
    super.initState();
    _audioService.initializeDemoHistory();
    _checkServer();
  }

  void _checkServer() async {
    final online = await _apiService.checkHealth();
    if (mounted) {
      setState(() {
        _isBackendOnline = online;
      });
    }
  }

  void _launchCallSimulation({
    required String name,
    required String number,
    required String scenario,
  }) {
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
                          onPressed: () {
                            _checkServer();
                            setModalState(() {});
                          },
                          child: const Text('Test', style: TextStyle(color: Color(0xFF38BDF8))),
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
              );
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
            const SizedBox(height: 20),

            // Statistics Grid
            _buildStatsGrid(),
            const SizedBox(height: 24),

            // Simulation Test Suite (Member 4 Demo Launcher)
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
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF38BDF8).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'MEMBER 4 FLOW',
                    style: TextStyle(
                      color: Color(0xFF38BDF8),
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
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
                    );
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
            },
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
            value: '42',
            icon: Icons.phone_callback_rounded,
            color: const Color(0xFF38BDF8),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildStatTile(
            title: 'Blocked',
            value: '14',
            icon: Icons.gpp_bad_rounded,
            color: const Color(0xFFEF4444),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildStatTile(
            title: 'Deepfakes',
            value: '8',
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
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF131B2E),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFF1E293B)),
          ),
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
        );
      }).toList(),
    );
  }
}
