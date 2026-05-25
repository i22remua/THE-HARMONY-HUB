import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:harmonyhub/features/auth/presentation/login_screen.dart';
import 'package:harmonyhub/features/auth/presentation/splash_screen.dart';
import 'package:harmonyhub/features/home/presentation/app_shell.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';
import 'package:harmonyhub/features/spotify/presentation/spotify_connect_screen.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  bool _showSplash = true;
  Timer? _splashTimer;

  @override
  void initState() {
    super.initState();
    _splashTimer = Timer(const Duration(milliseconds: 1400), () {
      if (!mounted) return;
      setState(() {
        _showSplash = false;
      });
    });
  }

  @override
  void dispose() {
    _splashTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_showSplash) {
      return const SplashScreen();
    }

    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const SplashScreen();
        }

        if (!snapshot.hasData) {
          return const LoginScreen();
        }

        return AnimatedBuilder(
          animation: SpotifySession.instance,
          builder: (context, _) {
            if (!SpotifySession.instance.isConnected) {
              return const SpotifyConnectScreen();
            }

            return const AppShell();
          },
        );
      },
    );
  }
}
