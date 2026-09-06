import 'dart:math';
import 'package:flutter/material.dart';
import '../models/call_analysis.dart';

class RiskMeter extends StatefulWidget {
  final int score;
  final RiskLevel level;
  final double size;
  final bool showBadge;
  final bool showDetails;
  final String? subtitle;

  const RiskMeter({
    super.key,
    required this.score,
    required this.level,
    this.size = 180,
    this.showBadge = true,
    this.showDetails = true,
    this.subtitle,
  });

  @override
  State<RiskMeter> createState() => _RiskMeterState();
}

class _RiskMeterState extends State<RiskMeter> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scoreAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _scoreAnimation = Tween<double>(begin: 0, end: widget.score.toDouble()).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
    _controller.forward();
  }

  @override
  void didUpdateWidget(covariant RiskMeter oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.score != widget.score) {
      _scoreAnimation = Tween<double>(
        begin: oldWidget.score.toDouble(),
        end: widget.score.toDouble(),
      ).animate(
        CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
      );
      _controller.reset();
      _controller.forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _scoreAnimation,
      builder: (context, child) {
        final currentScore = _scoreAnimation.value.toInt();
        final currentLevel = RiskLevel.fromScore(currentScore);

        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CustomPaint(
              size: Size(widget.size, widget.size),
              painter: _RiskMeterPainter(
                score: _scoreAnimation.value,
                color: currentLevel.color,
              ),
              child: SizedBox(
                width: widget.size,
                height: widget.size,
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'RISK SCORE',
                        style: TextStyle(
                          fontSize: widget.size * 0.075,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.5,
                          color: Colors.white70,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '$currentScore',
                        style: TextStyle(
                          fontSize: widget.size * 0.28,
                          fontWeight: FontWeight.w900,
                          color: Colors.white,
                          height: 1.0,
                        ),
                      ),
                      if (widget.showBadge) ...[
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            color: currentLevel.color.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: currentLevel.color.withValues(alpha: 0.8),
                              width: 1.2,
                            ),
                          ),
                          child: Text(
                            currentLevel.colorBadgeText,
                            style: TextStyle(
                              fontSize: widget.size * 0.07,
                              fontWeight: FontWeight.w800,
                              color: currentLevel.color,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
            if (widget.subtitle != null) ...[
              const SizedBox(height: 8),
              Text(
                widget.subtitle!,
                style: const TextStyle(
                  color: Colors.white60,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ],
        );
      },
    );
  }
}

class _RiskMeterPainter extends CustomPainter {
  final double score;
  final Color color;

  _RiskMeterPainter({
    required this.score,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (min(size.width, size.height) / 2) - 10;
    final strokeWidth = size.width * 0.085;

    // Background track arc
    final trackPaint = Paint()
      ..color = const Color(0xFF1E293B)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    // Outer glow aura
    final glowPaint = Paint()
      ..color = color.withValues(alpha: 0.25)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth + 6
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10);

    // Active progress arc
    final progressPaint = Paint()
      ..shader = const SweepGradient(
        startAngle: -pi * 1.25,
        endAngle: pi * 0.25,
        colors: [
          Color(0xFF10B981), // Safe Green
          Color(0xFFFBBF24), // Moderate Yellow
          Color(0xFFF97316), // High Orange
          Color(0xFFEF4444), // Critical Red
        ],
        stops: [0.0, 0.4, 0.7, 1.0],
        transform: GradientRotation(-pi * 0.75),
      ).createShader(Rect.fromCircle(center: center, radius: radius))
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    const startAngle = 0.75 * pi;
    const sweepAngleTotal = 1.5 * pi;
    final sweepAngleActive = (score.clamp(0, 100) / 100.0) * sweepAngleTotal;

    // Draw track
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngleTotal,
      false,
      trackPaint,
    );

    // Draw active glow & progress
    if (score > 0) {
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweepAngleActive,
        false,
        glowPaint,
      );

      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        sweepAngleActive,
        false,
        progressPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _RiskMeterPainter oldDelegate) {
    return oldDelegate.score != score || oldDelegate.color != color;
  }
}
