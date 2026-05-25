import 'package:flutter/material.dart';

class EditorialPanel extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final List<Color>? gradientColors;
  final Color borderColor;
  final Color? accentColor;
  final List<BoxShadow>? boxShadow;

  const EditorialPanel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(22),
    this.radius = 30,
    this.gradientColors,
    this.borderColor = const Color(0xFFE7DBCD),
    this.accentColor,
    this.boxShadow,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: borderColor),
        gradient: LinearGradient(
          colors:
              gradientColors ??
              const [Color(0xFFFFFCF8), Color(0xFFF7EFE4)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow:
            boxShadow ??
            const [
              BoxShadow(
                color: Color(0x121F2421),
                blurRadius: 20,
                offset: Offset(0, 12),
              ),
            ],
      ),
      child: Stack(
        children: [
          if (accentColor != null)
            Positioned(
              left: 0,
              right: 0,
              top: 0,
              child: Container(height: 5, color: accentColor),
            ),
          Padding(padding: padding, child: child),
        ],
      ),
    );
  }
}

class EditorialSectionHeader extends StatelessWidget {
  final String eyebrow;
  final String title;
  final String? subtitle;
  final Widget? trailing;

  const EditorialSectionHeader({
    super.key,
    required this.eyebrow,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                eyebrow,
                style: const TextStyle(
                  fontSize: 11,
                  letterSpacing: 1.5,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF7C7268),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 26,
                  height: 1.0,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF1F2421),
                ),
              ),
              if (subtitle != null) ...[
                const SizedBox(height: 8),
                Text(
                  subtitle!,
                  style: const TextStyle(
                    color: Color(0xFF5E645F),
                    height: 1.45,
                  ),
                ),
              ],
            ],
          ),
        ),
        if (trailing != null) ...[
          const SizedBox(width: 12),
          trailing!,
        ],
      ],
    );
  }
}

class EditorialStatPill extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color backgroundColor;

  const EditorialStatPill({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    this.backgroundColor = const Color(0x14FFFFFF),
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.white),
          const SizedBox(width: 8),
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: Color(0xFFE7E4DE),
                  fontSize: 10,
                  letterSpacing: 1.1,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
