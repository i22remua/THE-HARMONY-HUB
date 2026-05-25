import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/feedback/presentation/feedback_screen.dart';

class GeneratedPlaylistScreen extends StatelessWidget {
  final String recommendationId;
  final String recommendationTitle;
  final String playlistName;
  final String playlistUrl;
  final String? desiredOutcome;
  final List<String> queriesUsed;
  final List<Map<String, dynamic>> selectedTracks;
  final String explorationPreference;
  final int feedbackCount;
  final double sessionTasteWeight;
  final double stableTasteWeight;
  final String tasteProfileMode;
  final bool environmentMeasured;
  final bool useEnvironment;
  final String? environmentContext;
  final double? environmentConfidence;
  final double? environmentStabilityScore;
  final double? environmentSampleDensityHz;
  final String environmentUsageStatus;
  final String environmentUsageRationale;

  const GeneratedPlaylistScreen({
    super.key,
    required this.recommendationId,
    required this.recommendationTitle,
    required this.playlistName,
    required this.playlistUrl,
    required this.queriesUsed,
    required this.selectedTracks,
    required this.explorationPreference,
    required this.feedbackCount,
    required this.sessionTasteWeight,
    required this.stableTasteWeight,
    required this.tasteProfileMode,
    required this.environmentMeasured,
    required this.useEnvironment,
    required this.environmentUsageStatus,
    required this.environmentUsageRationale,
    this.environmentContext,
    this.environmentConfidence,
    this.environmentStabilityScore,
    this.environmentSampleDensityHz,
    this.desiredOutcome,
  });

  Future<void> _openSpotify() async {
    HapticFeedback.lightImpact();
    final uri = Uri.parse(playlistUrl);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  String _outcomeLabel(String value) {
    switch (value) {
      case 'mas_ligero':
        return 'más ligero/a';
      case 'mas_centrado':
        return 'más centrado/a';
      case 'mas_acompanado':
        return 'más acompañado/a';
      case 'mas_despierto':
      case 'mas_animado':
        return 'más despierto/a';
      case 'mas_calmado':
        return 'más calmado/a';
      default:
        return value;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF8F1E8), Color(0xFFF1E7DA), Color(0xFFE8EEE7)],
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
                      'Playlist generada',
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
                padding: const EdgeInsets.fromLTRB(24, 22, 24, 24),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(32),
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF204F46),
                      Color(0xFF34685F),
                      Color(0xFFB96A47),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x26000000),
                      blurRadius: 30,
                      offset: Offset(0, 16),
                    ),
                  ],
                ),
                child: Stack(
                  children: [
                    Positioned(
                      top: -8,
                      right: -12,
                      child: Container(
                        width: 108,
                        height: 108,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.08),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 7,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.14),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: const Text(
                            'PLAYLIST LISTA',
                            style: TextStyle(
                              color: Colors.white,
                              letterSpacing: 1.4,
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        const SizedBox(height: 18),
                        Text(
                          playlistName,
                          style: Theme.of(context).textTheme.headlineMedium
                              ?.copyWith(
                                color: Colors.white,
                                height: 0.96,
                                fontSize: 42,
                              ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          desiredOutcome == null
                              ? 'Tu playlist ya está preparada para acompañarte en este momento.'
                              : 'La he orientado a que la sesión te deje ${_outcomeLabel(desiredOutcome!)}.',
                          style: const TextStyle(
                            color: Color(0xFFF6F4EF),
                            height: 1.45,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(height: 18),
                      ],
                    ),
                  ],
                ),
              ),
              ),
              const SizedBox(height: 16),
              StaggeredReveal(
                order: 3,
                child: EditorialPanel(
                accentColor: const Color(0xFFC8845A),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const EditorialSectionHeader(
                      eyebrow: 'SIGUIENTE PASO',
                      title: 'Escúchala y cierra el ciclo con feedback.',
                      subtitle:
                          'Abrirla en Spotify, escucharla y luego contar cómo te sentó es lo que convierte esta sesión en aprendizaje útil.',
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: _openSpotify,
                      icon: const Icon(Icons.music_note_rounded),
                      label: const Text('Abrir en Spotify'),
                    ),
                    const SizedBox(height: 10),
                      OutlinedButton.icon(
                        onPressed: () {
                          HapticFeedback.mediumImpact();
                          Navigator.push(
                            context,
                            buildHarmonyRoute(
                              FeedbackScreen(
                                recommendationId: recommendationId,
                                recommendationTitle: recommendationTitle,
                              ),
                            ),
                          );
                      },
                      icon: const Icon(Icons.rate_review_outlined),
                      label: const Text('Ir a feedback'),
                    ),
                  ],
                ),
              ),
              ),
              if (selectedTracks.isNotEmpty) ...[
                const SizedBox(height: 16),
                StaggeredReveal(
                  order: 4,
                  child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Selección final',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 10),
                        ...selectedTracks
                            .take(12)
                            .map(
                              (track) => Padding(
                                padding: const EdgeInsets.only(bottom: 10),
                                child: Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFFFFCF8),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(
                                      color: const Color(0xFFE7DBCD),
                                    ),
                                  ),
                                  child: Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Container(
                                        width: 42,
                                        height: 42,
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFE3EEE8),
                                          borderRadius: BorderRadius.circular(
                                            14,
                                          ),
                                        ),
                                        child: const Icon(
                                          Icons.queue_music_rounded,
                                          color: Color(0xFF204F46),
                                        ),
                                      ),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              track['name']?.toString() ??
                                                  'Track',
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w700,
                                              ),
                                            ),
                                            const SizedBox(height: 3),
                                            Text(
                                              (track['artists']
                                                          as List<dynamic>? ??
                                                      [])
                                                  .join(', '),
                                              style: const TextStyle(
                                                color: Color(0xFF5E645F),
                                              ),
                                            ),
                                          ],
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
                ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
