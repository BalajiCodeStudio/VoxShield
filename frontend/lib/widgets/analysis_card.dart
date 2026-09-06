import 'package:flutter/material.dart';

class AnalysisCard extends StatelessWidget {
  final int deepfakeScore;
  final int scamScore;
  final int urgencyScore;
  final bool isCompact;

  const AnalysisCard({
    super.key,
    required this.deepfakeScore,
    required this.scamScore,
    required this.urgencyScore,
    this.isCompact = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(isCompact ? 10 : 14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B).withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF334155), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isCompact) ...[
            const Row(
              children: [
                Icon(Icons.analytics_outlined, size: 16, color: Colors.white70),
                SizedBox(width: 6),
                Text(
                  'DETECTION BREAKDOWN',
                  style: TextStyle(
                    color: Colors.white70,
                    fontWeight: FontWeight.w700,
                    fontSize: 11,
                    letterSpacing: 1.1,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
          ],
          _buildMetricRow(
            label: 'Deepfake Voice',
            value: deepfakeScore,
            icon: Icons.record_voice_over_rounded,
            activeColor: deepfakeScore > 50 ? const Color(0xFFEF4444) : const Color(0xFF10B981),
          ),
          SizedBox(height: isCompact ? 6 : 10),
          _buildMetricRow(
            label: 'Scam Intent',
            value: scamScore,
            icon: Icons.shield_outlined,
            activeColor: scamScore > 50 ? const Color(0xFFF97316) : const Color(0xFF10B981),
          ),
          SizedBox(height: isCompact ? 6 : 10),
          _buildMetricRow(
            label: 'Urgency Pressure',
            value: urgencyScore,
            icon: Icons.speed_rounded,
            activeColor: urgencyScore > 50 ? const Color(0xFFFBBF24) : const Color(0xFF10B981),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricRow({
    required String label,
    required int value,
    required IconData icon,
    required Color activeColor,
  }) {
    final normalized = (value.clamp(0, 100)) / 100.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(icon, size: 14, color: Colors.white60),
                const SizedBox(width: 6),
                Text(
                  label,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            Text(
              '$value%',
              style: TextStyle(
                color: activeColor,
                fontWeight: FontWeight.w800,
                fontSize: 13,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: normalized,
            minHeight: 5,
            backgroundColor: const Color(0xFF0F172A),
            valueColor: AlwaysStoppedAnimation<Color>(activeColor),
          ),
        ),
      ],
    );
  }
}
