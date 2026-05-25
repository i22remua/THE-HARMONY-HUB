import 'package:dio/dio.dart';
import 'package:harmonyhub/core/network/api_client.dart';
import 'package:harmonyhub/features/recommendation/data/recommendation_model.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';

class RecommendationService {
  Future<RecommendationModel> generateRecommendation({
    required String mood,
    required String goal,
    required int stressLevel,
    required int energyLevel,
    required String noiseCategory,
    String vocalPreference = 'indistinto',
    String intensityPreference = 'media',
    String explorationPreference = 'equilibrado',
    String popularityPreference = 'mixta',
    int sessionDurationMin = 20,
    String? desiredOutcome,
    bool useEnvironment = true,
    String? environmentContext,
    double? environmentVariability,
    double? environmentPeakDelta,
    double? environmentConfidence,
    double? transientRatio,
    int? burstCount,
  }) async {
    // Envía el contexto completo al backend y devuelve la recomendación de
    // sesión junto con el `recommendation_id` que enlaza el resto del flujo.
    try {
      final spotifyUserId = SpotifySession.instance.profile?['id']?.toString();
      final response = await ApiClient.dio.post(
        '/recommendations/generate',
        data: {
          'mood': mood,
          'goal': goal,
          'spotify_user_id': spotifyUserId,
          'stress_level': stressLevel,
          'energy_level': energyLevel,
          'noise_category': noiseCategory,
          'vocal_preference': vocalPreference,
          'intensity_preference': intensityPreference,
          'exploration_preference': explorationPreference,
          'popularity_preference': popularityPreference,
          'session_duration_min': sessionDurationMin,
          'desired_outcome': desiredOutcome,
          'use_environment': useEnvironment,
          'environment_context': environmentContext,
          'environment_variability': environmentVariability,
          'environment_peak_delta': environmentPeakDelta,
          'environment_confidence': environmentConfidence,
          'transient_ratio': transientRatio,
          'burst_count': burstCount,
        },
      );

      return RecommendationModel.fromJson(
        Map<String, dynamic>.from(response.data),
      );
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      final data = e.response?.data;
      throw Exception('Error recomendación: status=$status, detail=$data');
    } catch (e) {
      throw Exception('Error recomendación: $e');
    }
  }
}
