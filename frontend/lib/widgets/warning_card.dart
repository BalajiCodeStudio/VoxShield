import 'package:flutter/material.dart';
import '../models/call_analysis.dart';

class WarningCard extends StatefulWidget {
  final ScamWarning warning;
  final VoidCallback? onTap;
  final bool isCompact;

  const WarningCard({
    super.key,
    required this.warning,
    this.onTap,
    this.isCompact = false,
  });

  @override
  State<WarningCard> createState() => _WarningCardState();
}

class _WarningCardState extends State<WarningCard> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isCritical = widget.warning.severity == RiskLevel.critical;
    final color = widget.warning.severity.color;

    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1B2E).withValues(alpha: 0.95),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isCritical
                  ? color.withValues(alpha: _pulseAnimation.value)
                  : color.withValues(alpha: 0.5),
              width: isCritical ? 1.5 : 1.0,
            ),
            boxShadow: [
              if (isCritical)
                BoxShadow(
                  color: color.withValues(alpha: 0.2 * _pulseAnimation.value),
                  blurRadius: 8,
                  spreadRadius: 1,
                ),
            ],
          ),
          child: child,
        );
      },
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: widget.onTap,
          child: Padding(
            padding: EdgeInsets.symmetric(
              horizontal: 12,
              vertical: widget.isCompact ? 8 : 12,
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Icon indicator
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    widget.warning.icon,
                    color: color,
                    size: widget.isCompact ? 16 : 20,
                  ),
                ),
                const SizedBox(width: 10),

                // Content
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              widget.warning.title,
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w700,
                                fontSize: widget.isCompact ? 13 : 14,
                                letterSpacing: 0.2,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              widget.warning.category,
                              style: TextStyle(
                                color: color,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (!widget.isCompact && widget.warning.description.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          widget.warning.description,
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                            height: 1.3,
                          ),
                        ),
                      ],
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
}
