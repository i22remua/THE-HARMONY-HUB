import 'package:dio/dio.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:harmonyhub/core/network/api_client.dart';
import 'package:harmonyhub/features/spotify/data/spotify_playlist_model.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';

class SpotifyService {
  String _extractErrorDetail(Object? data) {
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.trim().isNotEmpty) {
        return detail.trim();
      }
    }
    final text = '$data'.trim();
    if (text.isEmpty || text == 'null') {
      return 'No se pudo generar la playlist en este momento.';
    }
    return text;
  }

  Future<Map<String, dynamic>> connectSpotify() async {
    // Ejecuta el flujo OAuth completo con Spotify y devuelve token + perfil.
    final loginResponse = await ApiClient.dio.get('/spotify/login-url');
    final authUrl = loginResponse.data['authorize_url'] as String;
    final expectedState = loginResponse.data['state'] as String;

    final callbackUrl = await FlutterWebAuth2.authenticate(
      url: authUrl,
      callbackUrlScheme: 'harmonyhub',
    );

    final uri = Uri.parse(callbackUrl);
    final code = uri.queryParameters['code'];
    final returnedState = uri.queryParameters['state'];
    final error = uri.queryParameters['error'];

    if (error != null) {
      throw Exception('Spotify devolvió error: $error');
    }

    if (code == null || returnedState == null) {
      throw Exception('No se recibió code/state desde Spotify');
    }

    if (returnedState != expectedState) {
      throw Exception('State inválido');
    }

    final exchangeResponse = await ApiClient.dio.post(
      '/spotify/exchange',
      data: {'code': code, 'state': returnedState},
    );

    final accessToken = exchangeResponse.data['access_token'] as String;
    final refreshToken = exchangeResponse.data['refresh_token'] as String?;
    final expiresIn = exchangeResponse.data['expires_in'] as int?;

    final profileResponse = await ApiClient.dio.post(
      '/spotify/me',
      data: {'access_token': accessToken},
    );

    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'expires_in': expiresIn,
      'profile': profileResponse.data,
    };
  }

  Future<String> _ensureFreshAccessToken({String? fallbackAccessToken}) async {
    final session = SpotifySession.instance;
    final currentAccessToken = session.accessToken ?? fallbackAccessToken;
    final refreshToken = session.refreshToken;

    if (currentAccessToken == null) {
      throw Exception('No hay access token de Spotify disponible');
    }

    if (!session.shouldRefreshAccessTokenSoon || refreshToken == null) {
      return currentAccessToken;
    }

    return _refreshSpotifyAccessToken(refreshToken);
  }

  Future<String> _refreshSpotifyAccessToken(String refreshToken) async {
    final response = await ApiClient.dio.post(
      '/spotify/refresh',
      data: {'refresh_token': refreshToken},
    );

    final accessToken = response.data['access_token'] as String;
    final nextRefreshToken =
        response.data['refresh_token'] as String? ?? refreshToken;
    final expiresIn = response.data['expires_in'] as int?;

    SpotifySession.instance.updateAccessToken(
      accessToken: accessToken,
      refreshToken: nextRefreshToken,
      expiresInSeconds: expiresIn,
    );

    return accessToken;
  }

  bool _isExpiredSpotifyTokenError(DioException error) {
    final detail = '${error.response?.data ?? ''}'.toLowerCase();
    return detail.contains('the access token expired') ||
        detail.contains('error perfil spotify: 401');
  }

  Future<List<SpotifyPlaylistModel>> getMyPlaylists({
    required String accessToken,
  }) async {
    // Recupera las playlists del usuario autenticado para mostrarlas en app.
    var effectiveAccessToken = await _ensureFreshAccessToken(
      fallbackAccessToken: accessToken,
    );
    Response<dynamic> response;

    try {
      response = await ApiClient.dio.post(
        '/spotify/my-playlists',
        data: {'access_token': effectiveAccessToken},
        options: Options(
          sendTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 30),
        ),
      );
    } on DioException catch (e) {
      if (!_isExpiredSpotifyTokenError(e) ||
          SpotifySession.instance.refreshToken == null) {
        rethrow;
      }

      effectiveAccessToken = await _refreshSpotifyAccessToken(
        SpotifySession.instance.refreshToken!,
      );
      response = await ApiClient.dio.post(
        '/spotify/my-playlists',
        data: {'access_token': effectiveAccessToken},
        options: Options(
          sendTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 30),
        ),
      );
    }

    final items = (response.data['items'] as List<dynamic>? ?? []);

    return items
        .map(
          (item) => SpotifyPlaylistModel.fromJson(item as Map<String, dynamic>),
        )
        .toList();
  }

  Future<Map<String, dynamic>> generateSpotifyPlaylist({
    required String accessToken,
    required String goal,
    required String mood,
    required int stressLevel,
    required int energyLevel,
    required String noiseCategory,
    required String recommendationId,
    required String recommendationTitle,
    required String vocalPreference,
    required String intensityPreference,
    required String explorationPreference,
    required String popularityPreference,
    required int sessionDurationMin,
    required String desiredOutcome,
    bool useEnvironment = true,

    // Nuevos datos del entorno acústico
    String? environmentContext,
    double? environmentVariability,
    double? environmentPeakDelta,
    double? environmentConfidence,
    double? transientRatio,
    int? burstCount,
  }) async {
    // Traduce la recomendación de sesión en una petición completa de generación
    // de playlist, incluyendo contexto, recommendation_id y entorno opcional.
    try {
      var effectiveAccessToken = await _ensureFreshAccessToken(
        fallbackAccessToken: accessToken,
      );

      Response<dynamic> response;
      try {
        response = await ApiClient.dio.post(
          '/spotify/generate-playlist',
          data: {
            'access_token': effectiveAccessToken,
            'goal': goal,
            'mood': mood,
            'stress_level': stressLevel,
            'energy_level': energyLevel,
            'noise_category': noiseCategory,
            'recommendation_id': recommendationId,
            'recommendation_title': recommendationTitle,
            'vocal_preference': vocalPreference,
            'intensity_preference': intensityPreference,
            'exploration_preference': explorationPreference,
            'popularity_preference': popularityPreference,
            'session_duration_min': sessionDurationMin,
            'desired_outcome': desiredOutcome,
            'use_environment': useEnvironment,

            // Perfil acústico refinado
            'environment_context': environmentContext,
            'environment_variability': environmentVariability,
            'environment_peak_delta': environmentPeakDelta,
            'environment_confidence': environmentConfidence,
            'transient_ratio': transientRatio,
            'burst_count': burstCount,
          },
          options: Options(
            sendTimeout: const Duration(seconds: 60),
            receiveTimeout: const Duration(seconds: 60),
          ),
        );
      } on DioException catch (e) {
        if (!_isExpiredSpotifyTokenError(e) ||
            SpotifySession.instance.refreshToken == null) {
          rethrow;
        }

        effectiveAccessToken = await _refreshSpotifyAccessToken(
          SpotifySession.instance.refreshToken!,
        );
        response = await ApiClient.dio.post(
          '/spotify/generate-playlist',
          data: {
            'access_token': effectiveAccessToken,
            'goal': goal,
            'mood': mood,
            'stress_level': stressLevel,
            'energy_level': energyLevel,
            'noise_category': noiseCategory,
            'recommendation_id': recommendationId,
            'recommendation_title': recommendationTitle,
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
          options: Options(
            sendTimeout: const Duration(seconds: 60),
            receiveTimeout: const Duration(seconds: 60),
          ),
        );
      }

      return Map<String, dynamic>.from(response.data);
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      final data = e.response?.data;
      final detail = _extractErrorDetail(data);

      if (status == 429) {
        throw Exception(detail);
      }
      if (status == 400) {
        throw Exception(detail);
      }
      if (status == 401) {
        throw Exception('Tu sesión de Spotify ha caducado. Vuelve a conectarla.');
      }

      throw Exception(
        'No se pudo generar la playlist. ${detail == 'null' ? '' : detail}',
      );
    } catch (e) {
      throw Exception('unexpected_error=$e');
    }
  }
}
