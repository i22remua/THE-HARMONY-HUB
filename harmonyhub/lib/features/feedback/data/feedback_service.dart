import 'package:dio/dio.dart';
import 'package:harmonyhub/core/network/api_client.dart';

class FeedbackService {
  Future<void> submitFeedback({
    required String recommendationId,
    required String recommendationTitle,
    required bool helpful,
    required String effect,
    required String postSessionState,
    String? comment,
    bool useForTasteProfile = true,
    String preferenceScope = 'both',
  }) async {
    // Envía al backend la valoración global de la sesión para cerrar el ciclo
    // de aprendizaje del sistema.
    await ApiClient.dio.post(
      '/feedback/',
      data: {
        'recommendation_id': recommendationId,
        'recommendation_title': recommendationTitle,
        'helpful': helpful,
        'effect': effect,
        'post_session_state': postSessionState,
        'comment': comment,
        'use_for_taste_profile': useForTasteProfile,
        'preference_scope': preferenceScope,
      },
      options: Options(
        sendTimeout: const Duration(seconds: 20),
        receiveTimeout: const Duration(seconds: 20),
      ),
    );
  }
}
