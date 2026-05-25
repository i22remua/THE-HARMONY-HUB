import 'package:harmonyhub/features/checkin/data/environment_audio_profile.dart';

class EnvironmentAudioDecision {
  final bool shouldUseForPersonalization;
  final String statusLabel;
  final String rationale;

  const EnvironmentAudioDecision({
    required this.shouldUseForPersonalization,
    required this.statusLabel,
    required this.rationale,
  });

  static const Set<String> _clearContexts = {
    'Silencio estable',
    'Ruido de fondo suave',
    'Actividad sonora moderada',
    'Espacio publico activo',
    'Espacio público activo',
    'Ruido continuo intenso',
  };

  static const Set<String> _ambiguousContexts = {
    'Picos intermitentes',
    'Entorno conversacional',
    'Entorno mixto',
  };

  factory EnvironmentAudioDecision.fromProfile(EnvironmentAudioProfile profile) {
    final confidence = profile.confidence;
    final density = profile.sampleDensityHz;
    final stability = profile.stabilityScore;
    final context = profile.environmentContext;

    final confidenceGate = confidence >= 0.52;
    final densityGate = density >= 3.0;
    final clearContext = _clearContexts.contains(context);
    final ambiguousContext = _ambiguousContexts.contains(context);
    final stabilityGate = stability >= 0.42;
    final ambiguityPenalty = ambiguousContext && confidence < 0.68;

    final shouldUse =
        confidenceGate &&
        densityGate &&
        !ambiguityPenalty &&
        (stabilityGate || clearContext);

    if (shouldUse) {
      return const EnvironmentAudioDecision(
        shouldUseForPersonalization: true,
        statusLabel: 'Entorno usable',
        rationale:
            'La medicion es lo bastante consistente y densa como para usarla en la personalizacion.',
      );
    }

    if (!confidenceGate) {
      return const EnvironmentAudioDecision(
        shouldUseForPersonalization: false,
        statusLabel: 'Lectura prudente',
        rationale:
            'La confianza global de la escucha es baja, asi que la tomo solo como referencia.',
      );
    }

    if (!densityGate) {
      return const EnvironmentAudioDecision(
        shouldUseForPersonalization: false,
        statusLabel: 'Muestra escasa',
        rationale:
            'La escucha tiene poca densidad de muestras y no conviene que condicione la recomendacion.',
      );
    }

    if (ambiguityPenalty) {
      return const EnvironmentAudioDecision(
        shouldUseForPersonalization: false,
        statusLabel: 'Entorno ambiguo',
        rationale:
            'He detectado un ambiente cambiante o irregular y prefiero no personalizar con una lectura ambigua.',
      );
    }

    return const EnvironmentAudioDecision(
      shouldUseForPersonalization: false,
      statusLabel: 'Uso informativo',
      rationale:
          'La escucha aporta contexto, pero aun no es lo bastante estable como para guiar la personalizacion.',
    );
  }
}
