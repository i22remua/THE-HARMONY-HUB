import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/checkin/presentation/checkin_screen.dart';
import 'package:harmonyhub/features/history/presentation/history_screen.dart';
import 'package:harmonyhub/features/preset_modes/presentation/preset_modes_screen.dart';
import 'package:harmonyhub/features/profile/presentation/user_learning_screen.dart';

class HomeSectionsScreen extends StatelessWidget {
  const HomeSectionsScreen({super.key});

  Widget _featureBlock({
    required BuildContext context,
    required String eyebrow,
    required String title,
    required String body,
    required IconData icon,
    required List<Color> colors,
    required VoidCallback onTap,
    double? height,
  }) {
    return SizedBox(
      height: height,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(32),
          child: Ink(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(32),
              gradient: LinearGradient(
                colors: colors,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x18000000),
                  blurRadius: 24,
                  offset: Offset(0, 12),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.16),
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: Icon(icon, color: Colors.white),
                ),
                const Spacer(),
                Text(
                  eyebrow,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11,
                    letterSpacing: 1.7,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  title,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Colors.white,
                    fontSize: 32,
                    height: 0.95,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  body,
                  style: const TextStyle(
                    color: Color(0xFFF7F3EF),
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _editorialTile({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String subtitle,
    required Color accent,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(28),
        child: Ink(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.88),
            borderRadius: BorderRadius.circular(28),
            border: Border.all(color: const Color(0xFFE8DCCD)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Icon(icon, color: accent),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 6),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: Color(0xFF5E645F),
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              const Icon(Icons.arrow_forward_rounded, color: Color(0xFF1E4B43)),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF7F3EC), Color(0xFFF1E6D8), Color(0xFFE7EEE7)],
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
                  Expanded(
                    child: Text(
                      'Explorar tu espacio',
                      style: Theme.of(
                        context,
                      ).textTheme.headlineMedium?.copyWith(fontSize: 28),
                    ),
                  ),
                  const HomeShortcutButton(),
                ],
              ),
              const SizedBox(height: 18),
              StaggeredReveal(
                order: 0,
                child: _featureBlock(
                  context: context,
                  eyebrow: 'RUTAS PRINCIPALES',
                  title:
                      'Aquí se abre el resto del producto sin recargar la portada.',
                  body:
                      'Mantengo el contenido útil, pero lo convierto en un mapa visual más claro para entrar en cada bloque con intención.',
                  icon: Icons.explore_outlined,
                  colors: const [
                    Color(0xFF15322F),
                    Color(0xFF24544B),
                    Color(0xFF397066),
                    Color(0xFFC78259),
                  ],
                  onTap: () {},
                  height: 300,
                ),
              ),
              const SizedBox(height: 16),
              StaggeredReveal(
                order: 1,
                child: SizedBox(
                height: 210,
                child: Row(
                  children: [
                    Expanded(
                      child: _featureBlock(
                        context: context,
                        eyebrow: 'EMPEZAR',
                        title: 'Check-in',
                        body: 'Entrar rápido en tu momento actual.',
                        icon: Icons.favorite_outline_rounded,
                        colors: const [Color(0xFF1A5048), Color(0xFF2E6A60)],
                onTap: () {
                  HapticFeedback.selectionClick();
                  Navigator.of(context).push(
                    buildHarmonyRoute(const CheckinScreen()),
                  );
                },
              ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _featureBlock(
                        context: context,
                        eyebrow: 'ATAJOS',
                        title: 'Modos',
                        body: 'Entrar directo en un tono ya preparado.',
                        icon: Icons.auto_awesome_outlined,
                        colors: const [Color(0xFFB96E4B), Color(0xFFD79973)],
                        onTap: () {
                          HapticFeedback.selectionClick();
                          Navigator.of(context).push(
                            buildHarmonyRoute(const PresetModesScreen()),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              ),
              const SizedBox(height: 18),
              const EditorialSectionHeader(
                eyebrow: 'ATAJOS',
                title: 'Más espacios',
              ),
              const SizedBox(height: 12),
              StaggeredReveal(
                order: 2,
                child: _editorialTile(
                context: context,
                icon: Icons.history_rounded,
                title: 'Historial',
                subtitle:
                    'Revisar sesiones pasadas, playlists generadas y cómo fue cada cierre.',
                accent: const Color(0xFF1E4B43),
                onTap: () {
                  HapticFeedback.selectionClick();
                  Navigator.of(context).push(
                    buildHarmonyRoute(const HistoryScreen()),
                  );
                },
              ),
              ),
              const SizedBox(height: 12),
              StaggeredReveal(
                order: 3,
                child: _editorialTile(
                context: context,
                icon: Icons.psychology_alt_outlined,
                title: 'Aprendizaje',
                subtitle:
                    'Ver qué patrones estoy detectando para afinar mejor tus próximas sesiones.',
                accent: const Color(0xFFB96E4B),
                onTap: () {
                  HapticFeedback.selectionClick();
                  Navigator.of(context).push(
                    buildHarmonyRoute(const UserLearningScreen()),
                  );
                },
              ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
