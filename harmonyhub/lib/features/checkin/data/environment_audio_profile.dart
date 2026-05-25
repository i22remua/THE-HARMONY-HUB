class EnvironmentAudioProfile {
  final double meanDb;
  final double medianDb;
  final double minDb;
  final double maxDb;
  final double stdDev;
  final double peakDelta;
  final double transientRatio;
  final int burstCount;
  final int measurementDurationMs;
  final int sampleCount;
  final double sampleDensityHz;
  final double stabilityScore;
  final String noiseCategory;
  final String environmentContext;
  final double confidence;

  const EnvironmentAudioProfile({
    required this.meanDb,
    required this.medianDb,
    required this.minDb,
    required this.maxDb,
    required this.stdDev,
    required this.peakDelta,
    required this.transientRatio,
    required this.burstCount,
    required this.measurementDurationMs,
    required this.sampleCount,
    required this.sampleDensityHz,
    required this.stabilityScore,
    required this.noiseCategory,
    required this.environmentContext,
    required this.confidence,
  });

  factory EnvironmentAudioProfile.empty() {
    return const EnvironmentAudioProfile(
      meanDb: 0,
      medianDb: 0,
      minDb: 0,
      maxDb: 0,
      stdDev: 0,
      peakDelta: 0,
      transientRatio: 0,
      burstCount: 0,
      measurementDurationMs: 0,
      sampleCount: 0,
      sampleDensityHz: 0,
      stabilityScore: 0,
      noiseCategory: 'quiet',
      environmentContext: 'Sin medir',
      confidence: 0,
    );
  }

  factory EnvironmentAudioProfile.fallback({
    required String noiseCategory,
    required String environmentContext,
    required double measuredDb,
  }) {
    return EnvironmentAudioProfile(
      meanDb: measuredDb,
      medianDb: measuredDb,
      minDb: measuredDb,
      maxDb: measuredDb,
      stdDev: 0,
      peakDelta: 0,
      transientRatio: 0,
      burstCount: 0,
      measurementDurationMs: 0,
      sampleCount: 0,
      sampleDensityHz: 0,
      stabilityScore: 0,
      noiseCategory: noiseCategory,
      environmentContext: environmentContext,
      confidence: 0,
    );
  }

  Map<String, dynamic> toPublicFirestoreMap() {
    return {
      'noise_category': noiseCategory,
      'measured_db': meanDb,
      'noise_mean_db': meanDb,
      'noise_median_db': medianDb,
      'noise_min_db': minDb,
      'noise_max_db': maxDb,
      'environment_context': environmentContext,
      'environment_variability': stdDev,
      'environment_peak_delta': peakDelta,
      'transient_ratio': transientRatio,
      'burst_count': burstCount,
      'measurement_duration_ms': measurementDurationMs,
      'sample_count': sampleCount,
      'sample_density_hz': sampleDensityHz,
      'stability_score': stabilityScore,
      'environment_confidence': confidence,
    };
  }
}
