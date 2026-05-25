import 'package:flutter/material.dart';
import 'package:harmonyhub/core/widgets/harmony_hub_brand.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [
              Color(0xFF102927),
              Color(0xFF1D4943),
              Color(0xFF3A6D65),
              Color(0xFFCA7E57),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Stack(
          children: [
            Positioned(
              top: -80,
              right: -40,
              child: Container(
                width: 240,
                height: 240,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white.withValues(alpha: 0.08),
                ),
              ),
            ),
            Positioned(
              bottom: -110,
              left: -20,
              child: Container(
                width: 280,
                height: 280,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white.withValues(alpha: 0.06),
                ),
              ),
            ),
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(28, 28, 28, 36),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    StaggeredReveal(
                      order: 0,
                      child: Container(
                      padding: const EdgeInsets.fromLTRB(14, 10, 18, 10),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.08),
                        ),
                      ),
                      child: const HarmonyHubBrand(
                        iconSize: 26,
                        fontSize: 14,
                        gap: 10,
                        stackedWordmark: false,
                        textColor: Colors.white,
                      ),
                    ),
                    ),
                    const Spacer(),
                    const StaggeredReveal(
                      order: 1,
                      child: Center(
                        child: HarmonyHubBrand(
                        iconSize: 104,
                        fontSize: 36,
                        gap: 18,
                        textColor: Colors.white,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    ),
                    const SizedBox(height: 28),
                    const StaggeredReveal(
                      order: 2,
                      child: Text(
                        'Tu momento, convertido en una sesión musical con intención.',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 46,
                          height: 0.92,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const StaggeredReveal(
                      order: 3,
                      child: Text(
                        'Estoy preparando tu espacio para que entrar se sienta más como un ritual breve que como una app técnica.',
                        style: TextStyle(
                          color: Color(0xFFF4F1EC),
                          fontSize: 16,
                          height: 1.5,
                        ),
                      ),
                    ),
                    const SizedBox(height: 18),
                    StaggeredReveal(
                      order: 5,
                      child: Row(
                      children: [
                        Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.14),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: const Center(
                            child: SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.2,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 14),
                        const Expanded(
                          child: Text(
                            'Cargando tu acceso, tu contexto y la experiencia completa.',
                            style: TextStyle(
                              color: Color(0xFFF4F1EC),
                              height: 1.45,
                            ),
                          ),
                        ),
                      ],
                    ),
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
}
