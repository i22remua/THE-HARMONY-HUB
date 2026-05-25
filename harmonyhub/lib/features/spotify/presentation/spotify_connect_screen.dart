import 'package:flutter/material.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/spotify/presentation/spotify_connect_button.dart';

class SpotifyConnectScreen extends StatelessWidget {
  const SpotifyConnectScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF7F3EC), Color(0xFFF2E7D9), Color(0xFFE7EEE7)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              final isCompactLayout =
                  constraints.maxWidth < 390 || constraints.maxHeight < 760;
              final heroTitleSize = isCompactLayout ? 36.0 : 42.0;
              final heroTitleHeight = isCompactLayout ? 0.98 : 0.94;
              final heroTopGap = isCompactLayout ? 36.0 : 56.0;

              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 40),
                child: Column(
                  children: [
                    StaggeredReveal(
                      order: 0,
                      child: Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(42),
                        gradient: const LinearGradient(
                          colors: [
                            Color(0xFF102926),
                            Color(0xFF1D4740),
                            Color(0xFF305F58),
                            Color(0xFFBF7B54),
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x26000000),
                            blurRadius: 34,
                            offset: Offset(0, 18),
                          ),
                        ],
                      ),
                      child: Stack(
                        children: [
                          Positioned(
                            top: -24,
                            right: -16,
                            child: Container(
                              width: 170,
                              height: 170,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.white.withValues(alpha: 0.08),
                              ),
                            ),
                          ),
                          Positioned(
                            bottom: -36,
                            left: -18,
                            child: Container(
                              width: 138,
                              height: 138,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: Colors.white.withValues(alpha: 0.07),
                              ),
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.fromLTRB(24, 20, 24, 28),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                SizedBox(height: heroTopGap),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 8,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(999),
                                    border: Border.all(
                                      color: Colors.white.withValues(
                                        alpha: 0.08,
                                      ),
                                    ),
                                  ),
                                  child: const Text(
                                    'SPOTIFY CONNECT',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 11,
                                      letterSpacing: 1.5,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 18),
                                Text(
                                  'Conecta tu cuenta de Spotify, dale play a tus emociones',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: heroTitleSize,
                                    height: heroTitleHeight,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    ),
                    const SizedBox(height: 18),
                    StaggeredReveal(
                      order: 1,
                      child: Container(
                      width: double.infinity,
                      decoration: const BoxDecoration(
                        color: Color(0xFFFFFCF8),
                        borderRadius: BorderRadius.vertical(
                          top: Radius.circular(36),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Padding(
                            padding: EdgeInsets.fromLTRB(20, 24, 20, 0),
                            child: EditorialSectionHeader(
                              eyebrow: 'CONECTAR TU CUENTA',
                              title: '¿Para qué sirve esto?',
                              subtitle:
                                  'No es un paso técnico más: es lo que convierte tu estado actual en una playlist reproducible y personalizada.',
                            ),
                          ),
                          const Padding(
                            padding: EdgeInsets.fromLTRB(20, 18, 20, 0),
                            child: SpotifyConnectButton(compact: false),
                          ),
                          const Padding(
                            padding: EdgeInsets.fromLTRB(20, 18, 20, 0),
                            child: _BenefitRow(
                              icon: Icons.queue_music_rounded,
                              title: 'Playlists reales',
                              body:
                                  'Cada propuesta podrá abrirse y escucharse directamente en tu cuenta de Spotify.',
                            ),
                          ),
                          const Padding(
                            padding: EdgeInsets.fromLTRB(20, 12, 20, 0),
                            child: _BenefitRow(
                              icon: Icons.psychology_alt_outlined,
                              title: 'Más personalización',
                              body:
                                  'Tu perfil musical ayuda a que las sesiones se sientan menos genéricas y más tuyas.',
                            ),
                          ),
                          const Padding(
                            padding: EdgeInsets.fromLTRB(20, 12, 20, 40),
                            child: _BenefitRow(
                              icon: Icons.auto_graph_rounded,
                              title: 'Mejor aprendizaje',
                              body:
                                  'Cada sesión útil deja una señal más clara para afinar mejor las siguientes.',
                            ),
                          ),
                        ],
                      ),
                    ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ),
      floatingActionButton: const SizedBox.shrink(),
    );
  }
}

class _BenefitRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;

  const _BenefitRow({
    required this.icon,
    required this.title,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return EditorialPanel(
      radius: 24,
      padding: const EdgeInsets.all(16),
      accentColor: const Color(0xFFC8845A),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: const Color(0xFFE8EFE8),
              borderRadius: BorderRadius.circular(15),
            ),
            child: Icon(icon, color: const Color(0xFF1E4B43)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF1F2421),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  body,
                  style: const TextStyle(
                    color: Color(0xFF5E645F),
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
