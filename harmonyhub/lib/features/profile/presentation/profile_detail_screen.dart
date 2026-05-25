import 'package:flutter/material.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/spotify/presentation/spotify_connect_button.dart';

class ProfileDetailScreen extends StatelessWidget {
  final String title;
  final IconData icon;
  final String eyebrow;
  final List<String> points;
  final bool showSpotifyConnect;

  const ProfileDetailScreen({
    super.key,
    required this.title,
    required this.icon,
    required this.eyebrow,
    required this.points,
    this.showSpotifyConnect = false,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title), actions: const [HomeShortcutButton()]),
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF8F1E8), Color(0xFFF1E7DA), Color(0xFFE7EDE7)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 28),
          children: [
            StaggeredReveal(
              order: 0,
              child: Container(
              padding: const EdgeInsets.fromLTRB(24, 22, 24, 24),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(30),
                gradient: const LinearGradient(
                  colors: [
                    Color(0xFF204F46),
                    Color(0xFF35685F),
                    Color(0xFFE8D7C7),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x22000000),
                    blurRadius: 24,
                    offset: Offset(0, 12),
                  ),
                ],
              ),
              child: Stack(
                children: [
                  Positioned(
                    top: -10,
                    right: -10,
                    child: Container(
                      width: 104,
                      height: 104,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.1),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 54,
                        height: 54,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.16),
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: Icon(icon, color: Colors.white, size: 28),
                      ),
                      const SizedBox(height: 18),
                      Text(
                        eyebrow,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          letterSpacing: 1.5,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.headlineMedium
                            ?.copyWith(
                              color: Colors.white,
                              height: 0.98,
                              fontSize: 38,
                            ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            ),
            if (showSpotifyConnect) ...[
              const SizedBox(height: 16),
              const SpotifyConnectButton(compact: false),
            ],
            const SizedBox(height: 16),
            StaggeredReveal(
              order: 1,
              child: EditorialPanel(
                accentColor: const Color(0xFFC8845A),
                child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ...points.map(
                      (point) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Padding(
                              padding: EdgeInsets.only(top: 5),
                              child: Icon(
                                Icons.circle,
                                size: 8,
                                color: Color(0xFF204F46),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                point,
                                style: const TextStyle(
                                  color: Color(0xFF5E645F),
                                  height: 1.45,
                                ),
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
            ),
          ],
        ),
      ),
    );
  }
}
