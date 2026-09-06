import 'dart:math';
import 'package:flutter/material.dart';
import '../models/call_analysis.dart';

class VoiceStatusWidget extends StatefulWidget {
  final VoiceAnalysisResult? voiceAnalysis;
  final Stream<List<double>>? waveformStream;
  final bool isLive;

  const VoiceStatusWidget({
    super.key,
    this.voiceAnalysis,
    this.waveformStream,
    this.isLive = false,
  });

  @override
  State<VoiceStatusWidget> createState() => _VoiceStatusWidgetState();
}

class _VoiceStatusWidgetState extends State<VoiceStatusWidget> {
  List<double> _waveformBars = List.generate(20, (index) => 0.2 + (sin(index) * 0.15).abs());

  @override
  void initState() {
    super.initState();
    widget.waveformStream?.listen((bars) {
      if (mounted) {
        setState(() {
          _waveformBars = bars;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final isAi = widget.voiceAnalysis?.isAiVoice ?? false;
    final confidence = (widget.voiceAnalysis?.confidence ?? 0.0) * 100;
    final badgeColor = isAi ? const Color(0xFFEF4444) : const Color(0xFF10B981);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B).withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isAi ? const Color(0xFFEF4444).withValues(alpha: 0.4) : const Color(0xFF334155),
          width: 1.2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: widget.isLive ? const Color(0xFFEF4444) : Colors.blueGrey,
                      shape: BoxShape.circle,
                      boxShadow: widget.isLive
                          ? [
                              BoxShadow(
                                color: const Color(0xFFEF4444).withValues(alpha: 0.6),
                                blurRadius: 6,
                                spreadRadius: 2,
                              )
                            ]
                          : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'VOICE BIOMETRICS',
                    style: TextStyle(
                      color: Colors.white70,
                      fontWeight: FontWeight.w700,
                      fontSize: 11,
                      letterSpacing: 1.2,
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: badgeColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: badgeColor.withValues(alpha: 0.6)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isAi ? Icons.record_voice_over_rounded : Icons.person_outline_rounded,
                      color: badgeColor,
                      size: 13,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      isAi ? 'AI CLONED (${confidence.toInt()}%)' : 'HUMAN VOICE',
                      style: TextStyle(
                        color: badgeColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Live audio waveform visualizer
          SizedBox(
            height: 36,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: _waveformBars.map((amp) {
                final barHeight = (amp.clamp(0.05, 1.0) * 36).toDouble();
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 100),
                  width: 3.5,
                  height: max(4.0, barHeight),
                  decoration: BoxDecoration(
                    color: isAi
                        ? Color.lerp(const Color(0xFFF97316), const Color(0xFFEF4444), amp)
                        : Color.lerp(const Color(0xFF06B6D4), const Color(0xFF10B981), amp),
                    borderRadius: BorderRadius.circular(3),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 10),

          // Voice profile text description
          Row(
            children: [
              const Icon(Icons.graphic_eq_rounded, size: 14, color: Colors.white38),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  widget.voiceAnalysis?.voiceProfile ?? 'Analyzing speech spectrum in real-time...',
                  style: const TextStyle(
                    color: Colors.white60,
                    fontSize: 11,
                    fontStyle: FontStyle.italic,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
