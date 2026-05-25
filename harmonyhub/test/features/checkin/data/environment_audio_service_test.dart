import 'package:flutter_test/flutter_test.dart';
import 'package:harmonyhub/features/checkin/data/environment_audio_service.dart';

void main() {
  group('EnvironmentAudioService', () {
    final service = EnvironmentAudioService();

    test('detects stable silence-like environments', () {
      final samples = List<double>.generate(
        40,
        (index) => 34.5 + ((index % 3) * 0.3),
      );

      final profile = service.buildProfileFromSamplesForTest(
        samples,
        durationMs: 5000,
      );

      expect(profile.environmentContext, 'Silencio estable');
      expect(profile.noiseCategory, 'quiet');
      expect(profile.stabilityScore, greaterThan(0.70));
      expect(profile.confidence, greaterThan(0.60));
    });

    test('detects intermittent peaks as non-stable environments', () {
      final samples = <double>[
        48,
        49,
        50,
        70,
        48,
        49,
        51,
        72,
        49,
        50,
        48,
        68,
        49,
        50,
        51,
        73,
        48,
        49,
        50,
        71,
        48,
        49,
        50,
        69,
        48,
        49,
        50,
        72,
        49,
        48,
      ];

      final profile = service.buildProfileFromSamplesForTest(
        samples,
        durationMs: 5000,
      );

      expect(
        profile.environmentContext,
        anyOf('Picos intermitentes', 'Entorno conversacional', 'Entorno mixto'),
      );
      expect(profile.noiseCategory, isNot('quiet'));
      expect(profile.stabilityScore, lessThan(0.70));
    });

    test('does not collapse peaky audio into stable silence', () {
      final meanSamples = List<double>.generate(
        40,
        (index) => 35.0 + ((index % 2) * 0.2),
      );
      final peakSamples = <double>[
        35,
        36,
        35,
        58,
        35,
        36,
        35,
        61,
        35,
        36,
        35,
        57,
        35,
        36,
        35,
        63,
        35,
        36,
        35,
        60,
        35,
        36,
        35,
        59,
        35,
        36,
        35,
        62,
        35,
        36,
        35,
        58,
        35,
        36,
        35,
        61,
        35,
        36,
        35,
        59,
      ];

      final profile = service.buildProfileFromMeanAndPeakSamplesForTest(
        meanSamples,
        peakSamples,
        durationMs: 5000,
      );

      expect(profile.environmentContext, isNot('Silencio estable'));
      expect(profile.peakDelta, greaterThan(10));
      expect(profile.transientRatio, greaterThan(0.08));
    });

    test('low sample density reduces confidence', () {
      final samples = List<double>.generate(
        24,
        (index) => 44 + ((index % 2) * 0.5),
      );

      final dense = service.buildProfileFromSamplesForTest(
        samples,
        durationMs: 3000,
      );
      final sparse = service.buildProfileFromSamplesForTest(
        samples,
        durationMs: 9000,
      );

      expect(dense.sampleDensityHz, greaterThan(sparse.sampleDensityHz));
      expect(dense.confidence, greaterThan(sparse.confidence));
    });

    test('detects suspiciously frozen microphone input', () {
      final meanSamples = List<double>.filled(40, 17.5);
      final peakSamples = List<double>.filled(40, 17.5);

      final looksFrozen = service.looksFrozenInputForTest(
        meanSamples,
        peakSamples,
      );

      expect(looksFrozen, isTrue);
    });
  });
}
