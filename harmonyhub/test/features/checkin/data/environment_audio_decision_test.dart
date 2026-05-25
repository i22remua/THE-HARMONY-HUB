import 'package:flutter_test/flutter_test.dart';
import 'package:harmonyhub/features/checkin/data/environment_audio_decision.dart';
import 'package:harmonyhub/features/checkin/data/environment_audio_profile.dart';

void main() {
  group('EnvironmentAudioDecision', () {
    test('uses clear and stable environments for personalization', () {
      final profile = EnvironmentAudioProfile(
        meanDb: 35,
        medianDb: 35,
        minDb: 34,
        maxDb: 36,
        stdDev: 0.8,
        peakDelta: 1.8,
        transientRatio: 0.02,
        burstCount: 0,
        measurementDurationMs: 5000,
        sampleCount: 40,
        sampleDensityHz: 8.0,
        stabilityScore: 0.84,
        noiseCategory: 'quiet',
        environmentContext: 'Silencio estable',
        confidence: 0.82,
      );

      final decision = EnvironmentAudioDecision.fromProfile(profile);

      expect(decision.shouldUseForPersonalization, isTrue);
      expect(decision.statusLabel, 'Entorno usable');
    });

    test('does not use sparse measurements even if they look calm', () {
      final profile = EnvironmentAudioProfile(
        meanDb: 40,
        medianDb: 40,
        minDb: 39,
        maxDb: 41,
        stdDev: 0.9,
        peakDelta: 1.5,
        transientRatio: 0.01,
        burstCount: 0,
        measurementDurationMs: 9000,
        sampleCount: 24,
        sampleDensityHz: 2.6,
        stabilityScore: 0.79,
        noiseCategory: 'quiet',
        environmentContext: 'Ruido de fondo suave',
        confidence: 0.67,
      );

      final decision = EnvironmentAudioDecision.fromProfile(profile);

      expect(decision.shouldUseForPersonalization, isFalse);
      expect(decision.statusLabel, 'Muestra escasa');
    });

    test('does not use ambiguous environments with modest confidence', () {
      final profile = EnvironmentAudioProfile(
        meanDb: 52,
        medianDb: 51,
        minDb: 46,
        maxDb: 68,
        stdDev: 4.8,
        peakDelta: 10.5,
        transientRatio: 0.18,
        burstCount: 5,
        measurementDurationMs: 5000,
        sampleCount: 38,
        sampleDensityHz: 7.6,
        stabilityScore: 0.34,
        noiseCategory: 'moderate',
        environmentContext: 'Picos intermitentes',
        confidence: 0.61,
      );

      final decision = EnvironmentAudioDecision.fromProfile(profile);

      expect(decision.shouldUseForPersonalization, isFalse);
      expect(decision.statusLabel, 'Entorno ambiguo');
    });
  });
}
