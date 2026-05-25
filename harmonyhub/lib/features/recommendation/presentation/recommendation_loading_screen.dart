import 'package:flutter/material.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';

class RecommendationLoadingScreen extends StatelessWidget {
  const RecommendationLoadingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Esta pantalla amortigua la latencia entre el check-in y la decisión del
    // backend para que el usuario perciba el paso como parte del ritual de
    // recomendación, no como un cambio brusco entre pantallas.
    return Scaffold(
      body: Stack(
        children: [
          DecoratedBox(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Color(0xFFF8F1E8),
                  Color(0xFFF0E6DA),
                  Color(0xFFE8EEE7),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Container(
                  padding: const EdgeInsets.fromLTRB(26, 28, 26, 26),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(34),
                    gradient: const LinearGradient(
                      colors: [Color(0xFFFFFCF8), Color(0xFFF6EEDF)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    border: Border.all(color: const Color(0xFFE6DACB)),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x141F2421),
                        blurRadius: 28,
                        offset: Offset(0, 14),
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Stack(
                        alignment: Alignment.center,
                        children: [
                          Container(
                            width: 104,
                            height: 104,
                            decoration: const BoxDecoration(
                              shape: BoxShape.circle,
                              color: Color(0xFFE7F0EA),
                            ),
                          ),
                          Container(
                            width: 78,
                            height: 78,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(26),
                              gradient: const LinearGradient(
                                colors: [Color(0xFF204F46), Color(0xFF2F675D)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                            ),
                            child: const Icon(
                              Icons.auto_awesome_rounded,
                              size: 38,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      Text(
                        'Estoy preparando tu recomendación',
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(height: 1.0, fontSize: 34),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Estoy leyendo tu check-in, cruzando tus respuestas y afinando el tipo de sesión que mejor puede acompañarte ahora.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Color(0xFF5E645F),
                          height: 1.45,
                        ),
                      ),
                      const SizedBox(height: 24),
                      const SizedBox(
                        width: 30,
                        height: 30,
                        child: CircularProgressIndicator(strokeWidth: 2.6),
                      ),
                      const SizedBox(height: 14),
                      const Text(
                        'Esto suele tardar solo unos segundos.',
                        style: TextStyle(
                          color: Color(0xFF6A6F6B),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SafeArea(
            child: Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Material(
                  color: Colors.white.withValues(alpha: 0.92),
                  shape: const CircleBorder(),
                  elevation: 2,
                  child: const HomeShortcutButton(),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
