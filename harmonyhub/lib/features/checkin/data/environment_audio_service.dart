import 'dart:async';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:noise_meter/noise_meter.dart';
import 'package:permission_handler/permission_handler.dart';

import 'package:harmonyhub/features/checkin/data/environment_audio_profile.dart';

class EnvironmentAudioException implements Exception {
  final String message;

  EnvironmentAudioException(this.message);

  @override
  String toString() => message;
}

class EnvironmentAudioService {
  static const int _warmupMillis = 650;
  static const int _minimumSampleCount = 24;
  static const int _maxExtraMeasurementMillis = 4000;

  final NoiseMeter _noiseMeter = NoiseMeter();
  StreamSubscription<NoiseReading>? _subscription;
  bool _isRunning = false;

  // Conserva por separado el suelo acústico y los picos del buffer. El
  // plugin `noise_meter` expone ambos, y si solo usamos `meanDecibel`
  // tendemos a infra-detectar conversación, actividad o ruido intermitente.
  // Ese era el origen más probable del sesgo hacia "Silencio estable".
  static _AudioDbSample _sanitizeSample(NoiseReading reading) {
    final mean = _sanitizeStaticDecibel(reading.meanDecibel);
    final peak = _sanitizeStaticDecibel(reading.maxDecibel);
    return _AudioDbSample(
      meanDb: mean,
      maxDb: peak != null && mean != null ? max(peak, mean) : peak,
    );
  }

  Future<EnvironmentAudioProfile> analyzeEnvironment({
    int durationSeconds = 5,
  }) async {
    if (_isRunning) {
      throw EnvironmentAudioException(
        'Ya se está realizando una medición del entorno.',
      );
    }

    final status = await Permission.microphone.request();
    if (!status.isGranted) {
      throw EnvironmentAudioException(
        'Necesito permiso de micrófono para analizar el entorno.',
      );
    }

    _isRunning = true;
    final samples = <_AudioDbSample>[];
    final stopwatch = Stopwatch()..start();

    try {
      _subscription = _noiseMeter.noise.listen(
        (NoiseReading reading) {
          if (stopwatch.elapsedMilliseconds < _warmupMillis) {
            return;
          }
          final sample = _sanitizeSample(reading);
          if (sample.isValid) {
            samples.add(sample);
          }
        },
        onError: (_) {},
        cancelOnError: false,
      );

      await Future.delayed(Duration(seconds: durationSeconds));
      while (samples.length < _minimumSampleCount &&
          stopwatch.elapsedMilliseconds <
              (durationSeconds * 1000) + _maxExtraMeasurementMillis) {
        await Future.delayed(const Duration(milliseconds: 250));
      }
      stopwatch.stop();

      await _subscription?.cancel();
      _subscription = null;

      if (samples.length < _minimumSampleCount) {
        throw EnvironmentAudioException(
          'No he podido obtener suficientes muestras de audio.',
        );
      }

      if (_looksFrozenInput(samples)) {
        throw EnvironmentAudioException(
          'La señal del micrófono parece demasiado plana o congelada. Prueba a repetir la medición o reiniciar el micrófono del dispositivo.',
        );
      }

      final effectiveDurationMs = max(
        0,
        stopwatch.elapsedMilliseconds - _warmupMillis,
      );

      return _buildProfile(samples, durationMs: effectiveDurationMs);
    } finally {
      _isRunning = false;
      await _subscription?.cancel();
      _subscription = null;
    }
  }

  void dispose() {
    _subscription?.cancel();
    _subscription = null;
  }

  static double? _sanitizeStaticDecibel(double value) {
    if (value.isNaN || value.isInfinite) return null;
    if (value < 10 || value > 130) return null;
    return value;
  }

  List<double> _smoothSamples(List<double> values) {
    if (values.length < 5) return [...values];

    final smoothed = <double>[];
    for (var i = 0; i < values.length; i++) {
      final start = max(0, i - 1);
      final end = min(values.length - 1, i + 1);
      final window = values.sublist(start, end + 1)..sort();
      smoothed.add(_median(window));
    }
    return smoothed;
  }

  bool _looksFrozenInput(List<_AudioDbSample> samples) {
    if (samples.length < _minimumSampleCount) return false;

    final meanValues = samples
        .map((sample) => sample.meanDb ?? sample.maxDb!)
        .toList();
    final peakValues = samples
        .map((sample) => sample.maxDb ?? sample.meanDb!)
        .toList();

    final meanRange = meanValues.reduce(max) - meanValues.reduce(min);
    final peakRange = peakValues.reduce(max) - peakValues.reduce(min);

    return meanRange < 0.2 && peakRange < 0.2;
  }

  /// Construye un perfil de audio del entorno a partir de las muestras
  /// recopiladas por el micrófono.
  ///
  /// Recibe una lista de valores de decibelios (samples) y calcula:
  ///  - promedio (mean) para estimar el nivel general de ruido.
  ///  - mediana (median) para reducir el efecto de picos extremos.
  ///  - valor mínimo y máximo para medir el rango dinámico.
  ///  - desviación estándar (stdDev) para cuantificar la variabilidad.
  ///  - peakDelta como la diferencia entre el pico y el valle.
  ///  - transientRatio para detectar cambios rápidos respecto a la media.
  ///  - burstCount para contar ráfagas de ruido brusco.
  ///
  /// Luego clasifica el ruido en una categoría general y deduce un contexto
  /// del entorno basado en múltiples métricas. Finalmente calcula una
  /// confianza del resultado en función de la cantidad y calidad de las
  /// muestras, y devuelve un objeto `EnvironmentAudioProfile` completo.
  EnvironmentAudioProfile _buildProfile(
    List<_AudioDbSample> samples, {
    required int durationMs,
  }) {
    final meanSamples = _smoothSamples(
      samples.map((sample) => sample.meanDb ?? sample.maxDb!).toList(),
    );
    final peakSamples = samples
        .map((sample) => sample.maxDb ?? sample.meanDb!)
        .toList();

    final meanSorted = [...meanSamples]..sort();
    final peakSorted = [...peakSamples]..sort();
    final trimmedMean = _trimExtremes(meanSorted);
    final trimmedPeak = _trimExtremes(peakSorted);

    final mean = trimmedMean.reduce((a, b) => a + b) / trimmedMean.length;
    final median = _median(meanSorted);
    final peakMean = trimmedPeak.reduce((a, b) => a + b) / trimmedPeak.length;
    final minDb = meanSorted.first;
    final maxDb = peakSorted.last;
    final stdDev = _stdDev(trimmedMean, mean);
    final lowBand = _percentile(meanSorted, 0.10);
    final highBand = _percentile(peakSorted, 0.90);
    final peakDelta = highBand - lowBand;
    final transientRatio = _transientRatio(peakSamples, median, stdDev);
    final burstCount = _burstCount(peakSamples, stdDev: stdDev);
    final sampleDensityHz = durationMs <= 0
        ? 0.0
        : (samples.length / (durationMs / 1000.0));
    final stabilityScore = _stabilityScore(
      stdDev: stdDev,
      peakDelta: peakDelta,
      transientRatio: transientRatio,
      burstCount: burstCount,
    );
    final environmentContext = _inferEnvironmentContext(
      meanDb: mean,
      medianDb: median,
      peakMeanDb: peakMean,
      stdDev: stdDev,
      peakDelta: peakDelta,
      transientRatio: transientRatio,
      burstCount: burstCount,
      stabilityScore: stabilityScore,
    );
    final noiseCategory = _classifyNoise(
      meanDb: mean,
      medianDb: median,
      peakMeanDb: peakMean,
      stdDev: stdDev,
      peakDelta: peakDelta,
      transientRatio: transientRatio,
      burstCount: burstCount,
      environmentContext: environmentContext,
      stabilityScore: stabilityScore,
    );
    final normalizedEnvironmentContext = _normalizeEnvironmentContext(
      noiseCategory: noiseCategory,
      environmentContext: environmentContext,
      stdDev: stdDev,
      peakDelta: peakDelta,
    );
    final confidence = _confidence(
      sampleCount: samples.length,
      sampleDensityHz: sampleDensityHz,
      stdDev: stdDev,
      peakDelta: peakDelta,
      transientRatio: transientRatio,
      burstCount: burstCount,
      environmentContext: normalizedEnvironmentContext,
      meanDb: mean,
      medianDb: median,
    );

    return EnvironmentAudioProfile(
      meanDb: mean,
      medianDb: median,
      minDb: minDb,
      maxDb: maxDb,
      stdDev: stdDev,
      peakDelta: peakDelta,
      transientRatio: transientRatio,
      burstCount: burstCount,
      measurementDurationMs: durationMs,
      sampleCount: samples.length,
      sampleDensityHz: sampleDensityHz,
      stabilityScore: stabilityScore,
      noiseCategory: noiseCategory,
      environmentContext: normalizedEnvironmentContext,
      confidence: confidence,
    );
  }

  double _median(List<double> sorted) {
    if (sorted.isEmpty) return 0;
    final mid = sorted.length ~/ 2;
    if (sorted.length.isOdd) return sorted[mid];
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }

  List<double> _trimExtremes(List<double> sorted) {
    if (sorted.length < 15) return [...sorted];

    final trimCount = max(1, (sorted.length * 0.10).floor());
    final start = trimCount;
    final end = sorted.length - trimCount;
    if (start >= end) return [...sorted];
    return sorted.sublist(start, end);
  }

  double _percentile(List<double> sorted, double percentile) {
    if (sorted.isEmpty) return 0;
    if (sorted.length == 1) return sorted.first;

    final clamped = percentile.clamp(0.0, 1.0);
    final index = clamped * (sorted.length - 1);
    final lower = index.floor();
    final upper = index.ceil();

    if (lower == upper) return sorted[lower];

    final fraction = index - lower;
    return sorted[lower] + ((sorted[upper] - sorted[lower]) * fraction);
  }

  double _stdDev(List<double> values, double mean) {
    if (values.isEmpty) return 0;
    final variance =
        values.map((v) => pow(v - mean, 2)).reduce((a, b) => a + b) /
        values.length;
    return sqrt(variance);
  }

  double _transientRatio(List<double> values, double center, double stdDev) {
    if (values.isEmpty) return 0;
    final threshold = max(4.0, stdDev * 1.2);
    final count = values.where((v) => (v - center).abs() >= threshold).length;
    return count / values.length;
  }

  int _burstCount(List<double> values, {required double stdDev}) {
    if (values.length < 2) return 0;

    var bursts = 0;
    var insideBurst = false;
    final jumpThreshold = max(4.5, stdDev * 1.35);
    final resetThreshold = max(2.5, stdDev * 0.70);

    for (var i = 1; i < values.length; i++) {
      final jump = (values[i] - values[i - 1]).abs();

      if (jump >= jumpThreshold && !insideBurst) {
        bursts++;
        insideBurst = true;
      } else if (jump < resetThreshold) {
        insideBurst = false;
      }
    }

    return bursts;
  }

  double _stabilityScore({
    required double stdDev,
    required double peakDelta,
    required double transientRatio,
    required int burstCount,
  }) {
    final stdComponent = (1.0 - (stdDev / 12.0)).clamp(0.0, 1.0); 
    final peakComponent = (1.0 - (peakDelta / 28.0)).clamp(0.0, 1.0);
    final transientComponent = (1.0 - (transientRatio / 0.35)).clamp(0.0, 1.0);
    final burstComponent = (1.0 - (burstCount / 8.0)).clamp(0.0, 1.0);
    return (stdComponent * 0.35 +
            peakComponent * 0.25 +
            transientComponent * 0.25 +
            burstComponent * 0.15)
        .clamp(0.0, 1.0);
  }

  String _classifyNoise({
    required double meanDb,
    required double medianDb,
    required double peakMeanDb,
    required double stdDev,
    required double peakDelta,
    required double transientRatio,
    required int burstCount,
    required String environmentContext,
    required double stabilityScore,
  }) {
    final effectiveDb =
        (medianDb * 0.55) + (meanDb * 0.20) + (peakMeanDb * 0.25);

    // Algunos dispositivos reportan un suelo artificialmente alto incluso en
    // entornos muy tranquilos. Si la señal es extremadamente estable, no la
    // tratamos como ruido fuerte solo por el valor absoluto.
    final suspiciousStableFloor =
        effectiveDb >= 68 &&
        stdDev <= 1.8 &&
        peakDelta <= 5.0 &&
        transientRatio <= 0.04 &&
        burstCount == 0;

    if (suspiciousStableFloor) {
      return 'moderate';
    }

    if (environmentContext == 'Silencio estable' && stabilityScore >= 0.70) {
      return 'quiet';
    }

    if (environmentContext == 'Ruido de fondo suave') {
      return effectiveDb < 50 ? 'quiet' : 'moderate';
    }

    if (environmentContext == 'Entorno conversacional') {
      return 'moderate';
    }

    if (environmentContext == 'Picos intermitentes') {
      return effectiveDb >= 62 ? 'active' : 'moderate';
    }

    if (environmentContext == 'Espacio público activo') {
      return effectiveDb >= 74 ? 'loud' : 'active';
    }

    if (environmentContext == 'Ruido continuo intenso') {
      return 'loud';
    }

    if (effectiveDb < 42) return 'quiet';
    if (effectiveDb < 56) return 'moderate';
    if (effectiveDb < 72) return 'active';
    return 'loud';
  }

  String _inferEnvironmentContext({
    required double meanDb,
    required double medianDb,
    required double peakMeanDb,
    required double stdDev,
    required double peakDelta,
    required double transientRatio,
    required int burstCount,
    required double stabilityScore,
  }) {
    final effectiveDb =
        (medianDb * 0.50) + (meanDb * 0.20) + (peakMeanDb * 0.30);

    // Nivel muy bajo y poca variación: es un ambiente silencioso y estable.
    if (effectiveDb < 40 &&
        stdDev < 2.2 &&
        peakDelta < 6 &&
        transientRatio < 0.06 &&
        stabilityScore >= 0.72) {
      return 'Silencio estable';
    }

    // Ruido leve y constante, con muy pocas ráfagas repentinas.
    if (effectiveDb < 52 &&
        stdDev < 4.0 &&
        transientRatio < 0.10 &&
        burstCount <= 1) {
      return 'Ruido de fondo suave';
    }

    // Niveles moderados con muchos cambios rápidos y varias ráfagas:
    // típico de una conversación en el mismo espacio.
    if (effectiveDb >= 42 &&
        effectiveDb < 61 &&
        transientRatio >= 0.14 &&
        burstCount >= 2 &&
        stdDev >= 2.8) {
      return 'Entorno conversacional';
    }

    // Gran diferencia entre pico y valle y varias ráfagas indica ruido
    // intermitente, como puertas, pasos o sonidos puntuales.
    if (peakDelta >= 14 && transientRatio >= 0.10 && burstCount >= 2) {
      return 'Picos intermitentes';
    }

    // Nivel alto pero con muchos transitorios: puede ser un lugar público
    // activo donde hay movimiento y voces discontínuas.
    if (effectiveDb >= 58 &&
        effectiveDb < 74 &&
        (transientRatio >= 0.10 || burstCount >= 3)) {
      return 'Espacio público activo';
    }

    // Nivel alto y estable sugiere un ruido continuo intenso como maquinaria
    // o tráfico, con poca variabilidad relativa.
    if (effectiveDb >= 66 && stdDev < 5.5 && transientRatio < 0.08) {
      return 'Ruido continuo intenso';
    }

    // Nivel moderado o alto con variabilidad importante es un entorno
    // sonoro activo pero no necesariamente conversacional.
    if (effectiveDb >= 50 && stdDev >= 4.0) {
      return 'Actividad sonora moderada';
    }

    // Si no encaja en las condiciones anteriores, se asume un entorno mixto.
    return 'Entorno mixto';
  }

  String _normalizeEnvironmentContext({
    required String noiseCategory,
    required String environmentContext,
    required double stdDev,
    required double peakDelta,
  }) {
    if (noiseCategory == 'quiet' &&
        environmentContext == 'Ruido continuo intenso') {
      return 'Silencio estable';
    }

    if (noiseCategory == 'moderate' &&
        environmentContext == 'Ruido continuo intenso') {
      if (stdDev <= 2.2 && peakDelta <= 6.0) {
        return 'Ruido de fondo suave';
      }
      return 'Entorno mixto';
    }

    if (noiseCategory == 'moderate' &&
        environmentContext == 'Espacio público activo') {
      return 'Actividad sonora moderada';
    }

    if (noiseCategory == 'active' && environmentContext == 'Silencio estable') {
      return 'Actividad sonora moderada';
    }

    return environmentContext;
  }

  double _confidence({
    required int sampleCount,
    required double sampleDensityHz,
    required double stdDev,
    required double peakDelta,
    required double transientRatio,
    required int burstCount,
    required String environmentContext,
    required double meanDb,
    required double medianDb,
  }) {
    var value = 0.30;
    value += min(sampleCount / 120.0, 0.24);
    value += min(sampleDensityHz / 18.0, 0.12); 

    final stableQuietContext =
        environmentContext == 'Silencio estable' ||
        environmentContext == 'Ruido de fondo suave';

    if (stableQuietContext) {
      value += stdDev <= 2.5 ? 0.12 : 0.05;
      value += peakDelta <= 8.0 ? 0.08 : 0.03;
    } else {
      value += min(stdDev / 12.0, 0.10);
      value += min(peakDelta / 35.0, 0.10);
      value += min(transientRatio, 0.08);
      value += min(burstCount / 8.0, 0.07);
    }

    final centralGap = (meanDb - medianDb).abs();
    if (centralGap > 6.0) {
      value -= 0.05;
    }

    if (sampleCount < _minimumSampleCount) {
      value -= 0.08;
    }

    if (sampleDensityHz < 4.0) {
      value -= 0.10;
    } else if (sampleDensityHz < 6.0) {
      value -= 0.04;
    }

    if (environmentContext == 'Entorno mixto') { 
      value -= 0.04;
    } else {
      value += 0.06;
    }

    return value.clamp(0.0, 0.95); 
  }

  @visibleForTesting
  EnvironmentAudioProfile buildProfileFromSamplesForTest(
    List<double> samples, {
    int durationMs = 5000,
  }) {
    return _buildProfile(
      samples
          .map((value) => _AudioDbSample(meanDb: value, maxDb: value))
          .toList(),
      durationMs: durationMs,
    );
  }

  @visibleForTesting
  EnvironmentAudioProfile buildProfileFromMeanAndPeakSamplesForTest(
    List<double> meanSamples,
    List<double> peakSamples, {
    int durationMs = 5000,
  }) {
    assert(meanSamples.length == peakSamples.length);
    return _buildProfile(
      List<_AudioDbSample>.generate(
        meanSamples.length,
        (index) => _AudioDbSample(
          meanDb: meanSamples[index],
          maxDb: peakSamples[index],
        ),
      ),
      durationMs: durationMs,
    );
  }

  @visibleForTesting
  bool looksFrozenInputForTest(
    List<double> meanSamples,
    List<double> peakSamples,
  ) {
    assert(meanSamples.length == peakSamples.length);
    return _looksFrozenInput(
      List<_AudioDbSample>.generate(
        meanSamples.length,
        (index) => _AudioDbSample(
          meanDb: meanSamples[index],
          maxDb: peakSamples[index],
        ),
      ),
    );
  }
}

class _AudioDbSample {
  final double? meanDb;
  final double? maxDb;

  const _AudioDbSample({required this.meanDb, required this.maxDb});

  bool get isValid => meanDb != null || maxDb != null;
}
