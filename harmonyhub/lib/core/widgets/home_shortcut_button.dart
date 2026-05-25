import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:harmonyhub/features/auth/presentation/login_screen.dart';
import 'package:harmonyhub/features/home/presentation/app_shell.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';
import 'package:harmonyhub/features/spotify/presentation/spotify_connect_screen.dart';

class HomeShortcutButton extends StatelessWidget {
  const HomeShortcutButton({super.key});

  Widget _destination() {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      return const LoginScreen();
    }
    if (!SpotifySession.instance.isConnected) {
      return const SpotifyConnectScreen();
    }
    return const AppShell(initialIndex: 0);
  }

  void _goHome(BuildContext context) {
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => _destination()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Ir a Home',
      onPressed: () => _goHome(context),
      icon: const Icon(Icons.home_rounded),
    );
  }
}
