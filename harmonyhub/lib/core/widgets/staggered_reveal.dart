import 'package:flutter/material.dart';

class StaggeredReveal extends StatelessWidget {
  final Widget child;
  final int order;
  final double offsetY;
  final Duration baseDelay;
  final Duration stepDelay;
  final Duration duration;

  const StaggeredReveal({
    super.key,
    required this.child,
    required this.order,
    this.offsetY = 18,
    this.baseDelay = const Duration(milliseconds: 60),
    this.stepDelay = const Duration(milliseconds: 90),
    this.duration = const Duration(milliseconds: 520),
  });

  @override
  Widget build(BuildContext context) {
    final totalDelayMs =
        baseDelay.inMilliseconds + (stepDelay.inMilliseconds * order);
    final totalDurationMs = totalDelayMs + duration.inMilliseconds;

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: Duration(milliseconds: totalDurationMs),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        final elapsedMs = value * totalDurationMs;
        final progress = ((elapsedMs - totalDelayMs) / duration.inMilliseconds)
            .clamp(0.0, 1.0);

        return Opacity(
          opacity: progress,
          child: Transform.translate(
            offset: Offset(0, offsetY * (1 - progress)),
            child: child,
          ),
        );
      },
      child: child,
    );
  }
}
