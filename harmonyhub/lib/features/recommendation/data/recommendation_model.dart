/// Representa la recomendación devuelta por FastAPI y reutilizada después en
/// Spotify y feedback para mantener enlazada toda la sesión.
class RecommendationModel {
  final String recommendationId;
  final String title;
  final String description;
  final String recommendedMode;
  final String targetBpmRange;
  final String targetEnergy;
  final String targetValence;
  final String? spotifyPlaylist;
  final String? catalogItemId;
  final String? catalogNoiseCategory;
  final bool mlEnabled;
  final double? modeMlProbability;
  final String selectionSource;
  final int feedbackCount;
  final double sessionTasteWeight;
  final double stableTasteWeight;
  final String tasteProfileMode;

  RecommendationModel({
    required this.recommendationId,
    required this.title,
    required this.description,
    required this.recommendedMode,
    required this.targetBpmRange,
    required this.targetEnergy,
    required this.targetValence,
    this.spotifyPlaylist,
    this.catalogItemId,
    this.catalogNoiseCategory,
    this.mlEnabled = false,
    this.modeMlProbability,
    this.selectionSource = 'heuristic',
    this.feedbackCount = 0,
    this.sessionTasteWeight = 0.0,
    this.stableTasteWeight = 0.0,
    this.tasteProfileMode = 'session_weighted',
  });

  factory RecommendationModel.fromJson(Map<String, dynamic> json) {
    return RecommendationModel(
      recommendationId: json['recommendation_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      recommendedMode: json['recommended_mode'] ?? '',
      targetBpmRange: json['target_bpm_range'] ?? '',
      targetEnergy: json['target_energy'] ?? '',
      targetValence: json['target_valence'] ?? '',
      spotifyPlaylist: json['spotify_playlist'],
      catalogItemId: json['catalog_item_id']?.toString(),
      catalogNoiseCategory: json['catalog_noise_category']?.toString(),
      mlEnabled: json['ml_enabled'] == true,
      modeMlProbability: (json['mode_ml_probability'] as num?)?.toDouble(),
      selectionSource: json['selection_source']?.toString() ?? 'heuristic',
      feedbackCount: (json['feedback_count'] as num?)?.toInt() ?? 0,
      sessionTasteWeight:
          (json['session_taste_weight'] as num?)?.toDouble() ?? 0.0,
      stableTasteWeight:
          (json['stable_taste_weight'] as num?)?.toDouble() ?? 0.0,
      tasteProfileMode:
          json['taste_profile_mode']?.toString() ?? 'session_weighted',
    );
  }
}
