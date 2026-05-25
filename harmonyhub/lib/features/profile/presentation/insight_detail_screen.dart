import 'package:flutter/material.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';

class InsightDetailScreen extends StatelessWidget {
  final String title;
  final String subtitle;
  final String body;

  const InsightDetailScreen({
    super.key,
    required this.title,
    required this.subtitle,
    required this.body,
  });

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
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.82),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: IconButton(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.arrow_back_rounded),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Text(
                      'Insight',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF1F2421),
                      ),
                    ),
                  ),
                  const HomeShortcutButton(),
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
                        Color(0xFF12312E),
                        Color(0xFF1E4B43),
                        Color(0xFF2F675E),
                        Color(0xFFE1D2C3),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x22000000),
                        blurRadius: 28,
                        offset: Offset(0, 16),
                      ),
                    ],
                  ),
                  child: Stack(
                    children: [
                      Positioned(
                        top: -28,
                        right: -20,
                        child: Container(
                          width: 180,
                          height: 180,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.08),
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 60,
                              height: 60,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.14),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: const Icon(
                                Icons.psychology_alt_outlined,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(height: 22),
                            const Text(
                              'LECTURA DEL SISTEMA',
                              style: TextStyle(
                                color: Color(0xFFF4F1EC),
                                fontSize: 11,
                                letterSpacing: 1.7,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 14),
                            Text(
                              title,
                              style: Theme.of(context).textTheme.headlineLarge
                                  ?.copyWith(
                                    color: Colors.white,
                                    fontSize: 42,
                                    height: 0.92,
                                  ),
                            ),
                            const SizedBox(height: 14),
                            Text(
                              subtitle,
                              style: const TextStyle(
                                color: Color(0xFFF5F1EC),
                                height: 1.45,
                                fontSize: 16,
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
                child: EditorialPanel(
                  radius: 32,
                  accentColor: const Color(0xFFC8845A),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const EditorialSectionHeader(
                        eyebrow: 'EXPLICACION',
                        title: 'Qué significa',
                      ),
                      const SizedBox(height: 12),
                      Text(
                        body,
                        style: const TextStyle(
                          color: Color(0xFF5E645F),
                          height: 1.6,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
