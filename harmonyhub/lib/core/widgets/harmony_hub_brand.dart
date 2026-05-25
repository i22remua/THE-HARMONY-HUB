import 'package:flutter/material.dart';

class HarmonyHubBrand extends StatelessWidget {
  final bool showWordmark;
  final bool stackedWordmark;
  final double iconSize;
  final double fontSize;
  final double gap;
  final Color textColor;
  final FontWeight fontWeight;

  const HarmonyHubBrand({
    super.key,
    this.showWordmark = true,
    this.stackedWordmark = true,
    this.iconSize = 64,
    this.fontSize = 18,
    this.gap = 14,
    this.textColor = const Color(0xFF1F2421),
    this.fontWeight = FontWeight.w700,
  });

  @override
  Widget build(BuildContext context) {
    final icon = HarmonyHubLogoIcon(size: iconSize);

    if (!showWordmark) {
      return icon;
    }

    final wordmark = stackedWordmark
        ? Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Harmony',
                style: TextStyle(
                  color: textColor,
                  fontSize: fontSize,
                  height: 0.92,
                  fontWeight: fontWeight,
                  letterSpacing: -0.6,
                ),
              ),
              Text(
                'Hub',
                style: TextStyle(
                  color: textColor,
                  fontSize: fontSize,
                  height: 0.92,
                  fontWeight: fontWeight,
                  letterSpacing: -0.6,
                ),
              ),
            ],
          )
        : Text(
            'Harmony Hub',
            style: TextStyle(
              color: textColor,
              fontSize: fontSize,
              height: 0.96,
              fontWeight: fontWeight,
              letterSpacing: -0.6,
            ),
          );

    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        icon,
        SizedBox(width: gap),
        Flexible(child: wordmark),
      ],
    );
  }
}

class HarmonyHubLogoIcon extends StatelessWidget {
  final double size;

  const HarmonyHubLogoIcon({super.key, this.size = 64});

  @override
  Widget build(BuildContext context) {
    final borderRadius = BorderRadius.circular(size * 0.28);

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: borderRadius,
        gradient: const LinearGradient(
          colors: [Color(0xFF184C3F), Color(0xFF2E7A5D), Color(0xFF8FD08B)],
          begin: Alignment.bottomLeft,
          end: Alignment.topRight,
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF184C3F).withValues(alpha: 0.24),
            blurRadius: size * 0.22,
            offset: Offset(0, size * 0.12),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: borderRadius,
        child: Stack(
          children: [
            Positioned(
              top: -size * 0.08,
              right: -size * 0.04,
              child: Container(
                width: size * 0.64,
                height: size * 0.64,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFFF1F7BA).withValues(alpha: 0.42),
                ),
              ),
            ),
            Positioned(
              top: size * 0.18,
              left: size * 0.12,
              child: _dot(size: size * 0.11),
            ),
            Positioned(
              top: size * 0.33,
              left: size * 0.08,
              child: _dot(size: size * 0.095),
            ),
            Positioned(
              top: size * 0.48,
              left: size * 0.05,
              child: _dot(size: size * 0.085),
            ),
            Positioned(
              left: -size * 0.02,
              right: -size * 0.02,
              top: size * 0.32,
              child: Transform.rotate(
                angle: -0.34,
                child: _band(
                  height: size * 0.16,
                  colors: const [
                    Color(0x00000000),
                    Color(0xFFBDE58A),
                    Color(0xFFEAF6A8),
                  ],
                ),
              ),
            ),
            Positioned(
              left: size * 0.02,
              right: -size * 0.08,
              top: size * 0.46,
              child: Transform.rotate(
                angle: -0.34,
                child: _band(
                  height: size * 0.15,
                  colors: const [
                    Color(0x00000000),
                    Color(0xFF82CD7E),
                    Color(0xFFCDEB8C),
                  ],
                ),
              ),
            ),
            Center(
              child: Transform.translate(
                offset: Offset(size * 0.03, size * 0.02),
                child: Icon(
                  Icons.music_note_rounded,
                  size: size * 0.72,
                  color: const Color(0xFFFFFBF3),
                  shadows: [
                    Shadow(
                      color: Colors.black.withValues(alpha: 0.16),
                      blurRadius: size * 0.08,
                      offset: Offset(size * 0.01, size * 0.02),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _dot({required double size}) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: const Color(0xFF9CD680),
        border: Border.all(
          color: const Color(0xFFF3F8C2).withValues(alpha: 0.7),
          width: size * 0.08,
        ),
      ),
    );
  }

  Widget _band({required double height, required List<Color> colors}) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(height),
        gradient: LinearGradient(
          colors: colors,
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        ),
      ),
    );
  }
}
