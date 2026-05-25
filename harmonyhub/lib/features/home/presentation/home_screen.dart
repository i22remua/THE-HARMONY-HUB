import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/harmony_hub_brand.dart';
import 'package:harmonyhub/features/auth/data/auth_service.dart';
import 'package:harmonyhub/features/auth/presentation/auth_gate.dart';
import 'package:harmonyhub/features/checkin/presentation/checkin_screen.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  String _greetingForHour(int hour) {
    if (hour < 12) return 'Buenos días';
    if (hour < 20) return 'Buenas tardes';
    return 'Buenas noches';
  }

  String _firstNameFromUser(User? user) {
    final displayName = user?.displayName?.trim();
    if (displayName != null && displayName.isNotEmpty) {
      return displayName.split(' ').first;
    }

    final email = user?.email?.trim();
    if (email != null && email.isNotEmpty) {
      return email.split('@').first;
    }

    return 'Alvaro';
  }

  Widget _miniPanel({
    required IconData icon,
    required String eyebrow,
    required String title,
    required String body,
    Color iconBackground = const Color(0xFFE8EFE8),
    Color accentColor = const Color(0xFF1E4B43),
  }) {
    return EditorialPanel(
      radius: 26,
      padding: const EdgeInsets.all(18),
      accentColor: accentColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: iconBackground,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: const Color(0xFF1E4B43)),
          ),
          const SizedBox(height: 18),
          Text(
            eyebrow,
            style: const TextStyle(
              fontSize: 11,
              letterSpacing: 1.4,
              fontWeight: FontWeight.w700,
              color: Color(0xFF7D7268),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              height: 1.05,
              fontWeight: FontWeight.w700,
              color: Color(0xFF1F2421),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            body,
            style: const TextStyle(color: Color(0xFF5E645F), height: 1.45),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authService = AuthService();
    final user = FirebaseAuth.instance.currentUser;
    final now = DateTime.now();
    final greeting = _greetingForHour(now.hour);
    final name = _firstNameFromUser(user);

    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF7F3EC), Color(0xFFF2E7D9), Color(0xFFE8EFE8)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 120),
            children: [
              Row(
                children: [
                  const Expanded(
                    child: HarmonyHubBrand(
                      iconSize: 42,
                      fontSize: 22,
                      gap: 12,
                      stackedWordmark: false,
                      textColor: Color(0xFF1F2421),
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.78),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: IconButton(
                      tooltip: 'Cerrar sesión',
                      onPressed: () async {
                        await authService.logout();
                        if (!context.mounted) return;
                        Navigator.of(context).pushAndRemoveUntil(
                          MaterialPageRoute(builder: (_) => const AuthGate()),
                          (route) => false,
                        );
                      },
                      icon: const Icon(Icons.logout_rounded),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              StaggeredReveal(
                order: 0,
                child: Container(
                  clipBehavior: Clip.antiAlias,
                  decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(40),
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF132E2B),
                      Color(0xFF214A43),
                      Color(0xFF3A6D65),
                      Color(0xFFC78259),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x22000000),
                      blurRadius: 30,
                      offset: Offset(0, 18),
                    ),
                  ],
                ),
                child: Stack(
                  children: [
                    Positioned(
                      top: -26,
                      right: -14,
                      child: Container(
                        width: 160,
                        height: 160,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.white.withValues(alpha: 0.09),
                        ),
                      ),
                    ),
                    Positioned(
                      bottom: -42,
                      left: -18,
                      child: Container(
                        width: 150,
                        height: 150,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.white.withValues(alpha: 0.07),
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Wrap(
                            spacing: 10,
                            runSpacing: 10,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 8,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(999),
                                  border: Border.all(
                                    color: Colors.white.withValues(alpha: 0.08),
                                  ),
                                ),
                                child: Text(
                                  '$greeting, $name',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 22),
                          const Text(
                            '¿Cómo te sientes hoy?',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 46,
                              height: 0.9,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 22),
                          Wrap(
                            spacing: 10,
                            runSpacing: 10,
                            children: [
                              FilledButton.icon(
                                onPressed: () {
                                  HapticFeedback.lightImpact();
                                  Navigator.push(
                                    context,
                                    buildHarmonyRoute(const CheckinScreen()),
                                  );
                                },
                                icon: const Icon(
                                  Icons.favorite_outline_rounded,
                                ),
                                label: const Text('Empezar check-in'),
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
              const SizedBox(height: 22),
              StaggeredReveal(
                order: 1,
                child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: _miniPanel(
                      icon: Icons.self_improvement_outlined,
                      eyebrow: 'RITMO',
                      title: 'Una entrada suave',
                      body:
                          'El check-in está pensado para que entres rápido, sin sentir que hablas con una interfaz fría.',
                      accentColor: const Color(0xFF1E4B43),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _miniPanel(
                      icon: Icons.auto_graph_outlined,
                      eyebrow: 'ENFOQUE',
                      title: 'Lectura con intención',
                      body:
                          'La app cruza emoción, objetivo, entorno y aprendizaje para preparar una sesión coherente.',
                      iconBackground: const Color(0xFFF3E3D6),
                      accentColor: const Color(0xFFC8845A),
                    ),
                  ),
                ],
              ),
              ),
              const SizedBox(height: 20),
              StaggeredReveal(
                order: 2,
                child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: _miniPanel(
                      icon: Icons.psychology_alt_outlined,
                      eyebrow: 'APRENDIZAJE',
                      title: 'Afinación progresiva',
                      body:
                          'Cada sesión útil deja una señal que ayuda a que las siguientes se parezcan más a ti.',
                      iconBackground: const Color(0xFFE5ECE8),
                      accentColor: const Color(0xFF5A7A6E),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _miniPanel(
                      icon: Icons.history_rounded,
                      eyebrow: 'MEMORIA',
                      title: 'Tu rastro reciente',
                      body:
                          'El historial te permite volver a sesiones, detectar patrones y entender qué te funciona mejor.',
                      iconBackground: const Color(0xFFF4E4D8),
                      accentColor: const Color(0xFFC8845A),
                    ),
                  ),
                ],
              ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
