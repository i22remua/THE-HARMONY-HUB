import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/features/spotify/data/spotify_service.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';

class SpotifyConnectButton extends StatefulWidget {
  final VoidCallback? onConnected;
  final bool compact;

  const SpotifyConnectButton({
    super.key,
    this.onConnected,
    this.compact = false,
  });

  @override
  State<SpotifyConnectButton> createState() => _SpotifyConnectButtonState();
}

class _SpotifyConnectButtonState extends State<SpotifyConnectButton> {
  final SpotifyService _spotifyService = SpotifyService();

  bool loading = false;
  String? displayName;
  String? email;

  @override
  void initState() {
    super.initState();
    final profile = SpotifySession.instance.profile;
    if (profile != null) {
      displayName = profile['display_name']?.toString();
      email = profile['email']?.toString();
    }
  }

  Future<void> _connect() async {
    HapticFeedback.mediumImpact();
    setState(() => loading = true);

    try {
      final result = await _spotifyService.connectSpotify();

      final accessToken = result['access_token'] as String;
      final refreshToken = result['refresh_token'] as String?;
      final expiresIn = result['expires_in'] as int?;
      final profile = result['profile'] as Map<String, dynamic>;

      SpotifySession.instance.setConnection(
        accessToken: accessToken,
        profile: profile,
        refreshToken: refreshToken,
        expiresInSeconds: expiresIn,
      );

      setState(() {
        displayName = profile['display_name']?.toString();
        email = profile['email']?.toString();
      });

      if (!mounted) return;
      HapticFeedback.selectionClick();
      widget.onConnected?.call();
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('No pude conectar Spotify: $e')));
    } finally {
      if (mounted) {
        setState(() => loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final connected = displayName != null;

    return EditorialPanel(
      radius: 28,
      accentColor: connected
          ? const Color(0xFF1DB954)
          : const Color(0xFF1E4B43),
      padding: EdgeInsets.all(widget.compact ? 18 : 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(
                  color: connected
                      ? const Color(0x1F1DB954)
                      : const Color(0x1F204F46),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Icon(
                  connected
                      ? Icons.check_circle_outline_rounded
                      : Icons.graphic_eq_rounded,
                  color: connected
                      ? const Color(0xFF1DB954)
                      : const Color(0xFF204F46),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'SPOTIFY',
                      style: TextStyle(
                        fontSize: 11,
                        letterSpacing: 1.7,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF7C7468),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      connected
                          ? 'Tu cuenta ya está lista'
                          : 'Conecta tu música real',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (connected && !widget.compact) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFFE7DBCD)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    displayName ?? 'Cuenta conectada',
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 16,
                    ),
                  ),
                  if (email != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      email!,
                      style: const TextStyle(color: Color(0xFF5E645F)),
                    ),
                  ],
                ],
              ),
            ),
          ],
          if (!widget.compact) ...[const SizedBox(height: 18)],
          FilledButton.icon(
            icon: loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.music_note_rounded),
            label: Text(
              loading
                  ? 'Conectando...'
                  : connected
                  ? 'Volver a enlazar Spotify'
                  : 'Conectar Spotify',
            ),
            onPressed: loading ? null : _connect,
          ),
        ],
      ),
    );
  }

}
