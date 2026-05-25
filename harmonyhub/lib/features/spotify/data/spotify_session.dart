import 'package:flutter/foundation.dart';

class SpotifySession extends ChangeNotifier {
  SpotifySession._();

  static final SpotifySession instance = SpotifySession._();

  String? _accessToken;
  String? _refreshToken;
  DateTime? _accessTokenExpiresAt;
  Map<String, dynamic>? _profile;

  String? get accessToken => _accessToken;
  String? get refreshToken => _refreshToken;
  DateTime? get accessTokenExpiresAt => _accessTokenExpiresAt;
  Map<String, dynamic>? get profile => _profile;
  bool get isConnected => _accessToken != null;
  bool get shouldRefreshAccessTokenSoon {
    final expiresAt = _accessTokenExpiresAt;
    if (_accessToken == null || expiresAt == null) {
      return false;
    }

    return DateTime.now().isAfter(
      expiresAt.subtract(const Duration(minutes: 2)),
    );
  }

  void setConnection({
    required String accessToken,
    required Map<String, dynamic> profile,
    String? refreshToken,
    int? expiresInSeconds,
  }) {
    _accessToken = accessToken;
    _refreshToken = refreshToken ?? _refreshToken;
    _accessTokenExpiresAt = expiresInSeconds != null
        ? DateTime.now().add(Duration(seconds: expiresInSeconds))
        : null;
    _profile = profile;
    notifyListeners();
  }

  void updateAccessToken({
    required String accessToken,
    String? refreshToken,
    int? expiresInSeconds,
  }) {
    _accessToken = accessToken;
    _refreshToken = refreshToken ?? _refreshToken;
    _accessTokenExpiresAt = expiresInSeconds != null
        ? DateTime.now().add(Duration(seconds: expiresInSeconds))
        : _accessTokenExpiresAt;
    notifyListeners();
  }

  void clear() {
    _accessToken = null;
    _refreshToken = null;
    _accessTokenExpiresAt = null;
    _profile = null;
    notifyListeners();
  }
}
