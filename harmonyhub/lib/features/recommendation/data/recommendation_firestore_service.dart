import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:harmonyhub/features/recommendation/data/recommendation_model.dart';

class RecommendationFirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  Future<void> saveRecommendation({
    required RecommendationModel recommendation,
    required String mood,
    required String goal,
    required int stressLevel,
    required int energyLevel,
    required String noiseCategory,
    required String vocalPreference,
    required String intensityPreference,
    required String explorationPreference,
    required String popularityPreference,
    required int sessionDurationMin,
    String? desiredOutcome,
    String? spotifyUserId,
    bool useEnvironment = true,
    bool environmentMeasured = false,
    String? environmentContext,
    double? environmentConfidence,
    double? environmentStabilityScore,
    double? environmentSampleDensityHz,
    String? environmentUsageStatus,
    String? environmentUsageRationale,
  }) async {
    final user = _auth.currentUser;
    if (user == null) {
      throw Exception('Usuario no autenticado');
    }

    await _firestore.collection('recommendations').add({
      'user_id': user.uid,
      'recommendation_id': recommendation.recommendationId,
      'spotify_user_id': spotifyUserId,
      'title': recommendation.title,
      'description': recommendation.description,
      'recommended_mode': recommendation.recommendedMode,
      'target_bpm_range': recommendation.targetBpmRange,
      'target_energy': recommendation.targetEnergy,
      'target_valence': recommendation.targetValence,
      'ml_enabled': recommendation.mlEnabled,
      'mode_ml_probability': recommendation.modeMlProbability,
      'selection_source': recommendation.selectionSource,
      'mood': mood,
      'goal': goal,
      'stress_level': stressLevel,
      'energy_level': energyLevel,
      'noise_category': noiseCategory,
      'vocal_preference': vocalPreference,
      'intensity_preference': intensityPreference,
      'exploration_preference': explorationPreference,
      'popularity_preference': popularityPreference,
      'session_duration_min': sessionDurationMin,
      'desired_outcome': desiredOutcome,
      'feedback_count': recommendation.feedbackCount,
      'session_taste_weight': recommendation.sessionTasteWeight,
      'stable_taste_weight': recommendation.stableTasteWeight,
      'taste_profile_mode': recommendation.tasteProfileMode,
      'use_environment': useEnvironment,
      'environment_measured': environmentMeasured,
      'environment_context': environmentContext,
      'environment_confidence': environmentConfidence,
      'environment_stability_score': environmentStabilityScore,
      'environment_sample_density_hz': environmentSampleDensityHz,
      'environment_usage_status': environmentUsageStatus,
      'environment_usage_rationale': environmentUsageRationale,
      'created_at': FieldValue.serverTimestamp(),
    });
  }
}
