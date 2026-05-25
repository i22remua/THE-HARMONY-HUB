import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/recommendation/data/recommendation_model.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';
import 'package:harmonyhub/features/spotify/data/generated_playlist_firestore_service.dart';
import 'package:harmonyhub/features/spotify/data/spotify_service.dart';
import 'package:harmonyhub/features/spotify/presentation/generated_playlist_screen.dart';

/// Pantalla que muestra la recomendación de sesión y permite convertirla en
/// una playlist real de Spotify.
class RecommendationScreen extends StatefulWidget {
  final RecommendationModel recommendation;
  final String goal;
  final String mood;
  final int stressLevel;
  final int energyLevel;
  final String noiseCategory;
  final String vocalPreference;
  final String intensityPreference;
  final String explorationPreference;
  final String popularityPreference;
  final String desiredOutcome;
  final int sessionDurationMin;
  final bool useEnvironment;
  final bool environmentMeasured;
  final String environmentUsageStatus;
  final String environmentUsageRationale;

  final String? environmentContext;
  final double? environmentVariability;
  final double? environmentPeakDelta;
  final double? environmentConfidence;
  final double? transientRatio;
  final int? burstCount;
  final double? environmentStabilityScore;
  final double? environmentSampleDensityHz;

  const RecommendationScreen({
    super.key,
    required this.recommendation,
    required this.goal,
    required this.mood,
    required this.stressLevel,
    required this.energyLevel,
    required this.noiseCategory,
    required this.vocalPreference,
    required this.intensityPreference,
    required this.explorationPreference,
    required this.popularityPreference,
    required this.sessionDurationMin,
    required this.desiredOutcome,
    required this.useEnvironment,
    required this.environmentMeasured,
    required this.environmentUsageStatus,
    required this.environmentUsageRationale,
    this.environmentContext,
    this.environmentVariability,
    this.environmentPeakDelta,
    this.environmentConfidence,
    this.transientRatio,
    this.burstCount,
    this.environmentStabilityScore,
    this.environmentSampleDensityHz,
  });

  @override
  State<RecommendationScreen> createState() => _RecommendationScreenState();
}

class _RecommendationScreenState extends State<RecommendationScreen> {
  final SpotifyService _spotifyService = SpotifyService();
  final GeneratedPlaylistFirestoreService _generatedPlaylistFirestoreService =
      GeneratedPlaylistFirestoreService();

  bool generatingPlaylist = false;
  bool mlEnabled = false;
  List<Map<String, dynamic>> selectedTracks = [];

  String _humanizeError(Object error) {
    final text = error.toString().replaceFirst('Exception: ', '').trim();
    if (text.startsWith('unexpected_error=')) {
      return 'No se pudo generar la playlist en este momento.';
    }
    return text;
  }

  String _goalLabel(String value) {
    switch (value) {
      case 'energia':
        return 'Recuperar impulso';
      case 'foco':
        return 'Concentrarme mejor';
      case 'relajacion':
        return 'Bajar revoluciones';
      default:
        return value;
    }
  }

  String _moodLabel(String value) {
    switch (value) {
      case 'feliz':
        return 'Feliz';
      case 'cansado':
        return 'Cansado/a';
      case 'agobiado':
        return 'Agobiado/a';
      case 'triste':
        return 'Bajo de ánimo';
      case 'neutral':
        return 'Neutral';
      default:
        return value;
    }
  }

  String _intensityLabel(String value) {
    switch (value) {
      case 'suave':
        return 'Intensidad suave';
      case 'media':
        return 'Intensidad media';
      case 'alta':
        return 'Intensidad alta';
      default:
        return value;
    }
  }

  String _desiredOutcomeLabel(String value) {
    switch (value) {
      case 'mas_ligero':
        return 'Acabar más ligero/a';
      case 'mas_centrado':
        return 'Acabar más centrado/a';
      case 'mas_acompanado':
        return 'Sentirme más acompañado/a';
      case 'mas_despierto':
      case 'mas_animado':
        return 'Acabar más despierto/a';
      case 'mas_calmado':
        return 'Acabar más calmado/a';
      default:
        return value;
    }
  }

  String _environmentInfluenceHeadline() {
    if (!widget.environmentMeasured) {
      return 'Hoy no he usado escucha del entorno';
    }
    if (widget.useEnvironment) {
      return 'Hoy el entorno sí ha influido en la recomendación';
    }
    return 'Hoy el entorno quedó como referencia, no como señal de control';
  }

  String _environmentInfluenceBody() {
    if (!widget.environmentMeasured) {
      return widget.environmentUsageRationale;
    }

    final confidenceText = ((widget.environmentConfidence ?? 0) * 100).round();
    final stabilityText =
        ((widget.environmentStabilityScore ?? 0) * 100).round();
    final densityText = widget.environmentSampleDensityHz?.toStringAsFixed(1);
    final metrics = <String>[
      if (widget.environmentContext != null &&
          widget.environmentContext!.trim().isNotEmpty)
        widget.environmentContext!,
      'confianza $confidenceText%',
      'estabilidad $stabilityText%',
      if (densityText != null) 'densidad $densityText Hz',
    ];

    if (widget.useEnvironment) {
      return 'He tomado el entorno como una pista real de personalización: ${metrics.join(' · ')}. ${widget.environmentUsageRationale}';
    }

    return 'La escucha detectó ${metrics.join(' · ')}, pero preferí no dejar que esa medición condicionara la sesión. ${widget.environmentUsageRationale}';
  }

  Widget _summaryChip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFFFFCF8), Color(0xFFF8F1E6)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE8DCCD)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A1F2421),
            blurRadius: 14,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: Color(0xFF1F2421),
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  String _learningSupportLabel() {
    final feedbackCount = widget.recommendation.feedbackCount;
    final stableWeight = widget.recommendation.stableTasteWeight;
    final sessionWeight = widget.recommendation.sessionTasteWeight;
    final totalWeight = stableWeight + sessionWeight;

    if (feedbackCount <= 0) {
      return 'Hoy todavía me apoyo poco en memoria aprendida y más en lo que me acabas de contar.';
    }

    if (totalWeight <= 0.01) {
      return 'Aunque ya existe memoria acumulada sobre ti, hoy no la aplico porque este estado emocional todavía no tiene evidencia suficiente para activarla con seguridad.';
    }

    if (widget.recommendation.tasteProfileMode == 'progressive_contextual') {
      return 'Hoy ya estoy aplicando una parte de lo aprendido sobre ti, pero con prudencia, porque este estado emocional aún está consolidando evidencia propia.';
    }

    if (widget.explorationPreference == 'familiar' && feedbackCount >= 3) {
      return 'Hoy me apoyo bastante en lo que he aprendido de tus sesiones y feedback anteriores.';
    }

    if (widget.explorationPreference == 'descubrir') {
      return 'Aunque tengo aprendizaje previo sobre ti, hoy le dejo más espacio a salir de esos patrones.';
    }

    if (feedbackCount >= 8 && stableWeight >= 0.14) {
      return 'Ya tengo una base razonable de aprendizaje sobre tus gustos y la estoy usando con bastante peso.';
    }

    if (feedbackCount >= 3) {
      return 'Ya hay algo de aprendizaje acumulado sobre tus gustos y hoy lo estoy mezclando con tu contexto actual.';
    }

    return 'Todavía estoy construyendo memoria sobre tus gustos, así que el peso principal sigue estando en tu check-in de hoy.';
  }

  String _learningDetailLabel() {
    final feedbackCount = widget.recommendation.feedbackCount;
    if (feedbackCount <= 0) {
      return 'Aún no tengo feedback histórico suficiente como para apoyarme mucho en tus patrones previos.';
    }
    return 'Base aprendida: $feedbackCount sesiones con feedback acumulado.';
  }

  String _effectiveIntensityForPlaylist() {
    final parts = widget.recommendation.recommendedMode.split('_');
    final candidate = parts.isNotEmpty ? parts.last : '';
    if (candidate == 'suave' || candidate == 'media' || candidate == 'alta') {
      return candidate;
    }
    return widget.intensityPreference;
  }

  String _weightLabel(double value) {
    final percentage = (value * 100).round();
    return '$percentage%';
  }

  String _trackCharacter(Map<String, dynamic> track) {
    final parts = <String>[];

    final energy = (track['energy_feature'] as num?)?.toDouble();
    final valence = (track['valence_feature'] as num?)?.toDouble();
    final instrumentalness = (track['instrumentalness'] as num?)?.toDouble();
    final bpm = (track['bpm'] as num?)?.toDouble();

    if (bpm != null && bpm > 0) {
      parts.add('${bpm.round()} BPM');
    }

    if (energy != null) {
      if (energy >= 0.72) {
        parts.add('con bastante impulso');
      } else if (energy >= 0.48) {
        parts.add('con energía equilibrada');
      } else {
        parts.add('más suave');
      }
    }

    if (valence != null) {
      if (valence >= 0.62) {
        parts.add('de tono luminoso');
      } else if (valence <= 0.38) {
        parts.add('de tono contenido');
      }
    }

    if (instrumentalness != null && instrumentalness >= 0.65) {
      parts.add('con aire instrumental');
    }

    if (parts.isEmpty) {
      return 'Encaja con la línea general de la sesión.';
    }

    final first = parts.first;
    final rest = parts.skip(1).toList();
    if (rest.isEmpty) {
      return first;
    }

    return '$first · ${rest.join(' · ')}';
  }

  Future<void> generateAutomaticPlaylist() async {
    // Llama al backend para generar la playlist final, la guarda en Firestore
    // y actualiza la UI con el resultado completo.
    final token = SpotifySession.instance.accessToken;
    if (token == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Conecta Spotify primero')));
      return;
    }

    HapticFeedback.mediumImpact();
    setState(() => generatingPlaylist = true);

    try {
      final effectiveIntensityPreference = _effectiveIntensityForPlaylist();

      // Este es el salto entre la recomendación abstracta y la sesión musical
      // real: el backend recibe contexto, consulta catálogo/ranking y devuelve
      // la playlist ya creada en Spotify.
      final result = await _spotifyService.generateSpotifyPlaylist(
        accessToken: token,
        goal: widget.goal,
        mood: widget.mood,
        stressLevel: widget.stressLevel,
        energyLevel: widget.energyLevel,
        noiseCategory: widget.noiseCategory,
        recommendationId: widget.recommendation.recommendationId,
        recommendationTitle: widget.recommendation.title,
        vocalPreference: widget.vocalPreference,
        intensityPreference: effectiveIntensityPreference,
        explorationPreference: widget.explorationPreference,
        popularityPreference: widget.popularityPreference,
        sessionDurationMin: widget.sessionDurationMin,
        desiredOutcome: widget.desiredOutcome,
        useEnvironment: widget.useEnvironment,
        environmentContext: widget.environmentContext,
        environmentVariability: widget.environmentVariability,
        environmentPeakDelta: widget.environmentPeakDelta,
        environmentConfidence: widget.environmentConfidence,
        transientRatio: widget.transientRatio,
        burstCount: widget.burstCount,
      );

      final playlistId = result['playlist_id']?.toString() ?? '';
      final playlistName = result['playlist_name']?.toString() ?? 'Harmony Hub';
      final playlistUrl = result['playlist_url']?.toString() ?? '';
      final tracksAdded = result['tracks_added'] as int? ?? 0;
      final recommendedMode =
          result['recommended_mode']?.toString() ??
          widget.recommendation.recommendedMode;
      final generationMode = result['generation_mode']?.toString();
      final queriesUsed = (result['queries_used'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList();
      final tracks = (result['selected_tracks'] as List<dynamic>? ?? [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      final backendMlEnabled = result['ml_enabled'] == true;
      final backendDesiredOutcome =
          result['desired_outcome']?.toString() ?? widget.desiredOutcome;
      final backendUseEnvironment =
          result['use_environment'] == true || widget.useEnvironment;
      final backendNoiseCategory =
          result['noise_category']?.toString() ??
          (backendUseEnvironment ? widget.noiseCategory : 'omitido');

      // Persistimos la playlist generada para mantener historial, detalle de
      // sesión y ciclo cerrado de feedback aunque el usuario abandone la vista.
      await _generatedPlaylistFirestoreService.saveGeneratedPlaylist(
        recommendationId: widget.recommendation.recommendationId,
        playlistId: playlistId,
        playlistName: playlistName,
        playlistUrl: playlistUrl,
        tracksAdded: tracksAdded,
        recommendedMode: recommendedMode,
        generationMode: generationMode,
        goal: widget.goal,
        noiseCategory: backendNoiseCategory,
        spotifyUserId: result['spotify_user_id']?.toString(),
        mlEnabled: backendMlEnabled,
        desiredOutcome: backendDesiredOutcome,
        feedbackCount: widget.recommendation.feedbackCount,
        sessionTasteWeight: widget.recommendation.sessionTasteWeight,
        stableTasteWeight: widget.recommendation.stableTasteWeight,
        tasteProfileMode: widget.recommendation.tasteProfileMode,
        environmentMeasured: widget.environmentMeasured,
        useEnvironment: backendUseEnvironment,
        environmentContext: widget.environmentContext,
        environmentConfidence: widget.environmentConfidence,
        environmentStabilityScore: widget.environmentStabilityScore,
        environmentSampleDensityHz: widget.environmentSampleDensityHz,
        environmentUsageStatus: widget.environmentUsageStatus,
        environmentUsageRationale: widget.environmentUsageRationale,
        selectedTracks: tracks,
      );

      if (!mounted) return;

      setState(() {
        selectedTracks = tracks;
        mlEnabled = widget.recommendation.mlEnabled || backendMlEnabled;
      });

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            backendMlEnabled
                ? 'Ya está. He preparado una playlist bastante afinada para este momento.'
                : 'Ya está. He preparado una playlist guiándome por tu momento de hoy.',
          ),
        ),
      );

      // La navegación final conserva todo el contexto útil para que la pantalla
      // de playlist pueda explicar qué se generó y con qué señales.
      Navigator.push(
        context,
        buildHarmonyRoute(
          GeneratedPlaylistScreen(
            recommendationId: widget.recommendation.recommendationId,
            recommendationTitle: widget.recommendation.title,
            playlistName: playlistName,
            playlistUrl: playlistUrl,
            desiredOutcome: backendDesiredOutcome,
            queriesUsed: queriesUsed,
            selectedTracks: tracks,
            explorationPreference: widget.explorationPreference,
            feedbackCount: widget.recommendation.feedbackCount,
            sessionTasteWeight: widget.recommendation.sessionTasteWeight,
            stableTasteWeight: widget.recommendation.stableTasteWeight,
            tasteProfileMode: widget.recommendation.tasteProfileMode,
            environmentMeasured: widget.environmentMeasured,
            useEnvironment: backendUseEnvironment,
            environmentContext: widget.environmentContext,
            environmentConfidence: widget.environmentConfidence,
            environmentStabilityScore: widget.environmentStabilityScore,
            environmentSampleDensityHz: widget.environmentSampleDensityHz,
            environmentUsageStatus: widget.environmentUsageStatus,
            environmentUsageRationale: widget.environmentUsageRationale,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(
        SnackBar(content: Text('Error generando playlist: ${_humanizeError(e)}')),
      );
    } finally {
      if (mounted) {
        setState(() => generatingPlaylist = false);
      }
    }
  }

  Widget _momentCard({
    required String eyebrow,
    required String value,
    required IconData icon,
  }) {
    return Container(
      width: 170,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFFFFCF8), Color(0xFFF7EFE4)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFE7DBCD)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x101F2421),
            blurRadius: 18,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: const Color(0xFFE8EFE8),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: const Color(0xFF1E4B43), size: 18),
          ),
          const SizedBox(height: 14),
          Text(
            eyebrow,
            style: const TextStyle(
              fontSize: 11,
              letterSpacing: 1.3,
              fontWeight: FontWeight.w700,
              color: Color(0xFF7C7268),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontSize: 18,
              height: 1.15,
              fontWeight: FontWeight.w700,
              color: Color(0xFF1F2421),
            ),
          ),
        ],
      ),
    );
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
          child: TweenAnimationBuilder<double>(
            duration: const Duration(milliseconds: 480),
            tween: Tween(begin: 0, end: 1),
            curve: Curves.easeOutCubic,
            builder: (context, value, child) {
              return Opacity(
                opacity: value,
                child: Transform.translate(
                  offset: Offset(0, 16 * (1 - value)),
                  child: child,
                ),
              );
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 40),
              children: [
                Row(
                  children: [
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.78),
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: IconButton(
                        onPressed: () => Navigator.of(context).maybePop(),
                        icon: const Icon(Icons.arrow_back_rounded),
                      ),
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text(
                        'Lo que te propongo hoy',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF1F2421),
                        ),
                      ),
                    ),
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.78),
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: const Padding(
                        padding: EdgeInsets.all(2),
                        child: HomeShortcutButton(),
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
                        Color(0xFF122E2A),
                        Color(0xFF204B44),
                        Color(0xFF39675F),
                        Color(0xFFC07A56),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x24000000),
                        blurRadius: 30,
                        offset: Offset(0, 18),
                      ),
                    ],
                  ),
                  child: Stack(
                    children: [
                      Positioned(
                        top: -24,
                        right: -18,
                        child: Container(
                          width: 154,
                          height: 154,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.08),
                          ),
                        ),
                      ),
                      Positioned(
                        bottom: -28,
                        left: -8,
                        child: Container(
                          width: 122,
                          height: 122,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.06),
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
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
                                (widget.recommendation.mlEnabled || mlEnabled)
                                    ? 'SESIÓN AFINADA CON APRENDIZAJE'
                                    : 'PROPUESTA CONSTRUIDA PARA ESTE MOMENTO',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 11,
                                  letterSpacing: 1.4,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            const SizedBox(height: 22),
                            Text(
                              widget.recommendation.title,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 44,
                                height: 0.92,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 16),
                            Text(
                              widget.recommendation.description,
                              style: const TextStyle(
                                color: Color(0xFFF6F4EF),
                                height: 1.45,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 20),
                            Wrap(
                              spacing: 10,
                              runSpacing: 10,
                              children: [
                                EditorialStatPill(
                                  label: 'MODO',
                                  value: widget.recommendation.title,
                                  icon: Icons.waves_rounded,
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
                const StaggeredReveal(
                  order: 1,
                  child: EditorialSectionHeader(
                    eyebrow: 'LECTURA RAPIDA',
                    title: 'Las señales que más han pesado hoy.',
                    subtitle:
                        'En lugar de una ficha técnica, aquí tienes una lectura más editorial de la sesión que acabo de construir.',
                  ),
                ),
                const SizedBox(height: 14),
                StaggeredReveal(
                  order: 2,
                  child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _momentCard(
                        eyebrow: 'OBJETIVO',
                        value: _goalLabel(widget.goal),
                        icon: Icons.track_changes_outlined,
                      ),
                      const SizedBox(width: 12),
                      _momentCard(
                        eyebrow: 'ANIMO',
                        value: _moodLabel(widget.mood),
                        icon: Icons.favorite_outline,
                      ),
                      const SizedBox(width: 12),
                      _momentCard(
                        eyebrow: 'INTENSIDAD',
                        value: _intensityLabel(widget.intensityPreference),
                        icon: Icons.graphic_eq_outlined,
                      ),
                      const SizedBox(width: 12),
                      _momentCard(
                        eyebrow: 'CIERRE BUSCADO',
                        value: _desiredOutcomeLabel(widget.desiredOutcome),
                        icon: Icons.flag_outlined,
                      ),
                    ],
                  ),
                ),
                ),
                const SizedBox(height: 16),
                StaggeredReveal(
                  order: 4,
                  child: EditorialPanel(
                  radius: 30,
                  accentColor: const Color(0xFF5F8377),
                  gradientColors: const [
                    Color(0xFFF6FBF8),
                    Color(0xFFEAF4EF),
                  ],
                  borderColor: const Color(0xFFDCE6E1),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _environmentInfluenceHeadline(),
                        style: const TextStyle(
                          fontSize: 22,
                          height: 1.0,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF17322D),
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        _environmentInfluenceBody(),
                        style: const TextStyle(
                          color: Color(0xFF29443F),
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
                ),
                const SizedBox(height: 16),
                StaggeredReveal(
                  order: 5,
                  child: EditorialPanel(
                  radius: 30,
                  accentColor: const Color(0xFF1E4B43),
                  gradientColors: const [
                    Color(0xFFF6FBF8),
                    Color(0xFFEAF4EF),
                  ],
                  borderColor: const Color(0xFFDCE6E1),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Cómo estoy usando lo aprendido de ti',
                        style: TextStyle(
                          fontSize: 22,
                          height: 1.0,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF17322D),
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        _learningSupportLabel(),
                        style: const TextStyle(
                          color: Color(0xFF29443F),
                          height: 1.5,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _learningDetailLabel(),
                        style: const TextStyle(
                          color: Color(0xFF4C615B),
                          height: 1.45,
                        ),
                      ),
                      const SizedBox(height: 14),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _summaryChip(
                            'Feedback acumulado: ${widget.recommendation.feedbackCount}',
                          ),
                          _summaryChip(
                            'Peso sesión ${_weightLabel(widget.recommendation.sessionTasteWeight)}',
                          ),
                          _summaryChip(
                            'Peso aprendido ${_weightLabel(widget.recommendation.stableTasteWeight)}',
                          ),
                          _summaryChip(
                            widget.recommendation.tasteProfileMode ==
                                    'stable_weighted'
                                ? 'Perfil más estable'
                                : widget.recommendation.tasteProfileMode ==
                                      'progressive_contextual'
                                ? 'Aprendizaje parcial'
                                : 'Perfil más contextual',
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                ),
                const SizedBox(height: 16),
                StaggeredReveal(
                  order: 6,
                  child: Container(
                  clipBehavior: Clip.antiAlias,
                  padding: const EdgeInsets.all(22),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(34),
                    gradient: const LinearGradient(
                      colors: [
                        Color(0xFF163832),
                        Color(0xFF245048),
                        Color(0xFF2F6258),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x22000000),
                        blurRadius: 24,
                        offset: Offset(0, 14),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Siguiente movimiento',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          letterSpacing: 1.2,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Si esta dirección te encaja, ahora la convierto en una playlist real dentro de Spotify.',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 26,
                          height: 1.08,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 18),
                      FilledButton.icon(
                        icon: generatingPlaylist
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.auto_awesome),
                        label: Text(
                          generatingPlaylist
                              ? 'Preparando tu playlist...'
                              : 'Preparar mi playlist',
                        ),
                        onPressed: generatingPlaylist
                            ? null
                            : generateAutomaticPlaylist,
                      ),
                    ],
                  ),
                ),
                ),
                if (selectedTracks.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  const StaggeredReveal(
                    order: 7,
                    child: Text(
                      'Selección resultante',
                      style: TextStyle(
                        fontSize: 24,
                        height: 1.0,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  ...selectedTracks.take(8).toList().asMap().entries.map((entry) {
                    final index = entry.key;
                    final track = entry.value;
                    return StaggeredReveal(
                      order: 8 + index,
                      child: Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFFCF8),
                          borderRadius: BorderRadius.circular(26),
                          border: Border.all(color: const Color(0xFFE7DBCD)),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                color: const Color(0xFFE8EFE8),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: const Icon(
                                Icons.queue_music_rounded,
                                color: Color(0xFF204F46),
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    track['name']?.toString() ?? 'Track',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 16,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    (track['artists'] as List<dynamic>? ?? [])
                                        .join(', '),
                                    style: const TextStyle(
                                      color: Color(0xFF5E645F),
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(_trackCharacter(track)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    );
                  }),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
