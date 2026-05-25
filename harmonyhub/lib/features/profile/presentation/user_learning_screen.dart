import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/profile/data/user_learning_firestore_service.dart';
import 'package:harmonyhub/features/profile/presentation/insight_detail_screen.dart';

class UserLearningScreen extends StatefulWidget {
  const UserLearningScreen({super.key});

  @override
  State<UserLearningScreen> createState() => _UserLearningScreenState();
}

class _UserLearningScreenState extends State<UserLearningScreen> {
  final UserLearningFirestoreService _service = UserLearningFirestoreService();

  Map<String, dynamic>? learningData;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _loadLearning();
  }

  Future<void> _loadLearning() async {
    try {
      final data = await _service.getMyLearningProfile();
      if (!mounted) return;
      setState(() {
        learningData = data;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No pude cargar esta parte ahora mismo: $e')),
      );
    }
  }

  double _blendedLearningSignal({
    required String legacyKey,
    required String sessionKey,
    required String stableKey,
    required int sessionCount,
    required int stableCount,
  }) {
    final sessionValue = (learningData?[sessionKey] as num?)?.toDouble();
    final stableValue =
        (learningData?[stableKey] as num?)?.toDouble() ??
        (learningData?[legacyKey] as num?)?.toDouble();

    if (sessionValue == null && stableValue == null) return 0.0;
    if (sessionValue == null) return stableValue!.clamp(0.0, 1.0);
    if (stableValue == null) return sessionValue.clamp(0.0, 1.0);

    final total = sessionCount + stableCount;
    if (total <= 0) return stableValue.clamp(0.0, 1.0);

    final sessionWeight = (sessionCount / total).clamp(0.25, 0.50);
    return ((stableValue * (1 - sessionWeight)) +
            (sessionValue * sessionWeight))
        .clamp(0.0, 1.0);
  }

  Widget _metricCard(String title, String value, IconData icon) {
    return Expanded(
      child: EditorialPanel(
        radius: 24,
        padding: const EdgeInsets.all(18),
        accentColor: const Color(0xFF1E4B43),
        child: Column(
          children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: const Color(0xFFE9F0EB),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: const Color(0xFF204F46)),
            ),
            const SizedBox(height: 10),
            Text(
              value,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 6),
            Text(title, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _heroCard(int feedbackCount, int positiveCount, double positiveRatio) {
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(34),
        gradient: const LinearGradient(
          colors: [
            Color(0xFF12312E),
            Color(0xFF1F4A43),
            Color(0xFF36665D),
            Color(0xFFC9865B),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x22000000),
            blurRadius: 26,
            offset: Offset(0, 16),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 22, 24, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'BASE APRENDIDA',
              style: TextStyle(
                color: Colors.white,
                fontSize: 11,
                letterSpacing: 1.5,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 14),
            const Text(
              'Tu evolución en Harmony Hub',
              style: TextStyle(
                color: Colors.white,
                fontSize: 34,
                height: 0.96,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _progressInsight({
    required String title,
    required String description,
    required double value,
    required Color color,
    required String detailBody,
  }) {
    return EditorialPanel(
      radius: 28,
      padding: EdgeInsets.zero,
      accentColor: color,
      child: InkWell(
        borderRadius: BorderRadius.circular(28),
        onTap: () {
          HapticFeedback.selectionClick();
          Navigator.push(
            context,
            buildHarmonyRoute(
              InsightDetailScreen(
                title: title,
                subtitle: description,
                body: detailBody,
              ),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                description,
                style: const TextStyle(color: Color(0xFF5E645F), height: 1.4),
              ),
              const SizedBox(height: 14),
              ClipRRect(
                borderRadius: BorderRadius.circular(999),
                child: LinearProgressIndicator(
                  minHeight: 12,
                  value: value,
                  backgroundColor: const Color(0xFFF1E5D8),
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
              ),
              const SizedBox(height: 10),
              Text(
                '${(value * 100).round()}%',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 10),
              Row(
                children: const [
                  Icon(
                    Icons.touch_app_outlined,
                    size: 16,
                    color: Color(0xFF6A6F6B),
                  ),
                  SizedBox(width: 6),
                  Text(
                    'Tocar para ver el insight completo',
                    style: TextStyle(
                      color: Color(0xFF6A6F6B),
                      fontSize: 12.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final feedbackCount =
        (learningData?['session_feedback_count'] as num?)?.toInt() ??
        (learningData?['feedback_count'] as num?)?.toInt() ??
        0;
    final positiveCount =
        (learningData?['session_positive_feedback_count'] as num?)?.toInt() ??
        (learningData?['positive_feedback_count'] as num?)?.toInt() ??
        0;
    final negativeCount =
        (learningData?['session_negative_feedback_count'] as num?)?.toInt() ??
        (learningData?['negative_feedback_count'] as num?)?.toInt() ??
        0;
    final positiveRatio = feedbackCount == 0
        ? 0.0
        : positiveCount / feedbackCount;
    final sessionFeedbackCount =
        (learningData?['session_feedback_count'] as num?)?.toInt() ?? 0;
    final stableFeedbackCount =
        (learningData?['stable_feedback_count'] as num?)?.toInt() ?? 0;
    final displayedValence = _blendedLearningSignal(
      legacyKey: 'preferred_valence',
      sessionKey: 'session_preferred_valence',
      stableKey: 'stable_preferred_valence',
      sessionCount: sessionFeedbackCount,
      stableCount: stableFeedbackCount,
    );
    final displayedEnergy = _blendedLearningSignal(
      legacyKey: 'preferred_energy',
      sessionKey: 'session_preferred_energy',
      stableKey: 'stable_preferred_energy',
      sessionCount: sessionFeedbackCount,
      stableCount: stableFeedbackCount,
    );
    final displayedDanceability = _blendedLearningSignal(
      legacyKey: 'preferred_danceability',
      sessionKey: 'session_preferred_danceability',
      stableKey: 'stable_preferred_danceability',
      sessionCount: sessionFeedbackCount,
      stableCount: stableFeedbackCount,
    );

    return Scaffold(
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadLearning,
              child: DecoratedBox(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Color(0xFFF8F1E8),
                      Color(0xFFF0E7DA),
                      Color(0xFFE7EDE7),
                    ],
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
                            child: Text(
                              'Perfil de aprendizaje',
                              style: TextStyle(
                                fontSize: 28,
                                fontWeight: FontWeight.w700,
                                color: Color(0xFF1F2421),
                              ),
                            ),
                          ),
                          Container(
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.82),
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: IconButton(
                              onPressed: _loadLearning,
                              icon: const Icon(Icons.refresh_rounded),
                            ),
                          ),
                          const SizedBox(width: 10),
                          const HomeShortcutButton(),
                        ],
                      ),
                      const SizedBox(height: 16),
                      StaggeredReveal(
                        order: 0,
                        child: _heroCard(
                          feedbackCount,
                          positiveCount,
                          positiveRatio,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          _metricCard(
                            'Sesiones valoradas',
                            '$feedbackCount',
                            Icons.forum_outlined,
                          ),
                          const SizedBox(width: 12),
                          _metricCard(
                            'Te ayudaron',
                            '$positiveCount',
                            Icons.thumb_up_alt_outlined,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          _metricCard(
                            'No encajaron',
                            '$negativeCount',
                            Icons.thumb_down_alt_outlined,
                          ),
                          const SizedBox(width: 12),
                          _metricCard(
                            'Afinidad positiva',
                            '${(positiveRatio * 100).round()}%',
                            Icons.favorite_outline,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      StaggeredReveal(
                        order: 1,
                        child: _progressInsight(
                          title: 'Tono emocional que suele sentarte mejor',
                          description:
                              'Cuanto más alto, más parecen ayudarte sesiones con un tono emocional luminoso o reparador.',
                          value: displayedValence,
                          color: const Color(0xFFB86A47),
                          detailBody:
                              'Este insight resume el tono emocional que con más frecuencia aparece en las sesiones que mejor te sientan. No significa que siempre necesites música positiva, sino que ese tipo de tono parece ayudarte más a menudo.',
                        ),
                      ),
                      StaggeredReveal(
                        order: 2,
                        child: _progressInsight(
                          title: 'Nivel de energía que mejor encaja contigo',
                          description:
                              'Esta pista resume si te suelen ir mejor sesiones suaves, equilibradas o con más impulso.',
                          value: displayedEnergy,
                          color: const Color(0xFF35685F),
                          detailBody:
                              'Aquí se concentra la señal de cuánta activación suele funcionarte mejor. Sirve para orientar futuras playlists hacia un punto más suave o más enérgico según tu historial real.',
                        ),
                      ),
                      StaggeredReveal(
                        order: 3,
                        child: _progressInsight(
                          title: 'Movimiento y ritmo habitual',
                          description:
                              'Aquí se refleja si normalmente te acompañan mejor playlists más calmadas o con más ritmo.',
                          value: displayedDanceability,
                          color: const Color(0xFF6C7C8A),
                          detailBody:
                              'Este valor recoge cuánto ritmo suele estar presente en las sesiones que terminan funcionando bien contigo. Es una guía, no una regla rígida.',
                        ),
                      ),
                      const SizedBox(height: 24),
                      Text(
                        'Tono emocional: ${displayedValence.toStringAsFixed(2)} · Energía: ${displayedEnergy.toStringAsFixed(2)} · Ritmo: ${displayedDanceability.toStringAsFixed(2)}',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Color(0xFF6A6F6B),
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Estos índices mezclan perfil estable y aprendizaje reciente.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Color(0xFF7A807C),
                          fontSize: 12.5,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
    );
  }
}
