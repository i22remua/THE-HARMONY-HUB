import 'dart:io' show Platform;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

class ApiClient {
  static const String _configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );
  // Cambia esta IP cuando tu Mac esté en otra Wi-Fi. El emulador Android
  // usará antes 10.0.2.2 y, si falla, probará automáticamente esta URL LAN.
  static const String _localNetworkBaseUrl = 'http://172.20.10.3:8000';
  static const String _androidEmulatorBaseUrl = 'http://10.0.2.2:8000';

  static List<String> _buildBaseUrlCandidates() {
    if (_configuredBaseUrl.isNotEmpty) {
      return [_configuredBaseUrl];
    }

    if (kIsWeb) {
      return ['http://localhost:8000'];
    }

    if (Platform.isAndroid) {
      return [_androidEmulatorBaseUrl, _localNetworkBaseUrl];
    }

    if (Platform.isIOS) {
      return [_localNetworkBaseUrl];
    }

    return [_localNetworkBaseUrl];
  }

  static final List<String> _baseUrlCandidates = _buildBaseUrlCandidates();
  static int _activeBaseUrlIndex = 0;

  static String get currentBaseUrl => _baseUrlCandidates[_activeBaseUrlIndex];

  static bool _isRetryableNetworkError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionError:
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.sendTimeout:
        return true;
      case DioExceptionType.badCertificate:
      case DioExceptionType.badResponse:
      case DioExceptionType.cancel:
      case DioExceptionType.unknown:
        return false;
    }
  }

  static Future<void> _retryWithNextBaseUrl(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final requestOptions = error.requestOptions;
    final triedBaseUrls = <String>{
      if (requestOptions.baseUrl.isNotEmpty) requestOptions.baseUrl,
      ...((requestOptions.extra['triedBaseUrls'] as List<dynamic>?) ?? []).map(
        (item) => item.toString(),
      ),
    };

    final nextIndex = _baseUrlCandidates.indexWhere(
      (candidate) => !triedBaseUrls.contains(candidate),
    );

    if (nextIndex == -1) {
      handler.next(error);
      return;
    }

    _activeBaseUrlIndex = nextIndex;

    final retriedRequest = requestOptions.copyWith(
      baseUrl: currentBaseUrl,
      extra: {
        ...requestOptions.extra,
        'triedBaseUrls': [...triedBaseUrls, currentBaseUrl],
      },
    );

    try {
      final response = await dio.fetch<dynamic>(retriedRequest);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  static final Dio dio =
      Dio(
          BaseOptions(
            baseUrl: currentBaseUrl,
            connectTimeout: const Duration(seconds: 20),
            receiveTimeout: const Duration(seconds: 60),
            sendTimeout: const Duration(seconds: 60),
            headers: {'Content-Type': 'application/json'},
          ),
        )
        ..interceptors.add(
          InterceptorsWrapper(
            onRequest: (options, handler) {
              options.baseUrl = currentBaseUrl;
              handler.next(options);
            },
            onError: (error, handler) async {
              if (_baseUrlCandidates.length <= 1 ||
                  !_isRetryableNetworkError(error)) {
                handler.next(error);
                return;
              }

              await _retryWithNextBaseUrl(error, handler);
            },
          ),
        );
}
