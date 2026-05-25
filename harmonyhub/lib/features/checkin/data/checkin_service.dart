import 'package:dio/dio.dart';
import 'package:harmonyhub/core/network/api_client.dart';

class CheckinService {
  Future<void> createCheckin({
    required String mood,
    required String goal,
    required int stressLevel,
    required int energyLevel,
    required String noiseCategory,
  }) async {
    // Registra el check-in mínimo en backend antes de pedir la recomendación.
    try {
      await ApiClient.dio.post(
        '/checkins/',
        data: {
          'mood': mood,
          'goal': goal,
          'stress_level': stressLevel,
          'energy_level': energyLevel,
          'noise_category': noiseCategory,
        },
      );
    } on DioException catch (e) {
      throw Exception(
        'No se pudo guardar el check-in. '
        'status=${e.response?.statusCode}, '
        'data=${e.response?.data}, '
        'message=${e.message}',
      );
    } catch (e) {
      throw Exception('No se pudo guardar el check-in: $e');
    }
  }
}
