import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/core/widgets/harmony_hub_brand.dart';
import 'package:harmonyhub/features/auth/data/auth_service.dart';
import 'package:harmonyhub/features/auth/presentation/auth_gate.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final AuthService _authService = AuthService();
  final TextEditingController emailController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();

  bool isLogin = true;
  bool loading = false;
  bool obscurePassword = true;

  String? _validateEmail(String email) {
    if (email.isEmpty) {
      return 'Escribe tu correo electrónico.';
    }

    final emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
    if (!emailPattern.hasMatch(email)) {
      return 'Ese correo no parece válido.';
    }

    return null;
  }

  String? _validatePassword(String password) {
    if (password.isEmpty) {
      return 'Escribe tu contraseña.';
    }

    if (!isLogin && password.length < 6) {
      return 'La contraseña debe tener al menos 6 caracteres.';
    }

    return null;
  }

  String _friendlyAuthMessage(Object error) {
    if (error is FirebaseAuthException) {
      switch (error.code) {
        case 'invalid-email':
          return 'El correo no tiene un formato válido.';
        case 'user-not-found':
        case 'wrong-password':
        case 'invalid-credential':
          return 'El correo o la contraseña no coinciden.';
        case 'email-already-in-use':
          return 'Ya existe una cuenta con ese correo.';
        case 'weak-password':
          return 'La contraseña es demasiado débil.';
        case 'too-many-requests':
          return 'Hay demasiados intentos. Espera un momento y vuelve a probar.';
        case 'network-request-failed':
          return 'No hay conexión suficiente para continuar.';
      }
    }

    return 'No pude continuar ahora mismo.';
  }

  String _friendlyResetMessage(Object error) {
    if (error is FirebaseAuthException) {
      switch (error.code) {
        case 'user-not-found':
          return 'No encuentro ninguna cuenta registrada con ese correo.';
        case 'invalid-email':
          return 'El correo no tiene un formato válido.';
        case 'too-many-requests':
          return 'Hay demasiados intentos. Espera un momento y vuelve a probar.';
        case 'network-request-failed':
          return 'No hay conexión suficiente para enviar el correo.';
      }
    }

    return _friendlyAuthMessage(error);
  }

  Future<void> submit() async {
    final email = emailController.text.trim();
    final password = passwordController.text.trim();
    final emailError = _validateEmail(email);
    final passwordError = _validatePassword(password);

    if (emailError != null || passwordError != null) {
      final message = emailError ?? passwordError!;
      HapticFeedback.lightImpact();
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
      return;
    }

    FocusScope.of(context).unfocus();
    HapticFeedback.mediumImpact();
    setState(() => loading = true);

    try {
      if (isLogin) {
        await _authService.login(email: email, password: password);
      } else {
        await _authService.register(email: email, password: password);
      }

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        buildHarmonyRoute(const AuthGate()),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_friendlyAuthMessage(e))));
    } finally {
      if (mounted) {
        setState(() => loading = false);
      }
    }
  }

  Future<void> _resetPassword() async {
    final email = emailController.text.trim();
    final emailError = _validateEmail(email);
    if (emailError != null) {
      HapticFeedback.lightImpact();
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(emailError)));
      return;
    }

    try {
      await _authService.sendPasswordReset(email: email);
      if (!mounted) return;
      HapticFeedback.selectionClick();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Te he enviado un correo para recuperar la contraseña a $email.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(_friendlyResetMessage(e))));
    }
  }

  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  Widget _authToggle(BuildContext context) {
    final activeColor = Theme.of(context).colorScheme.primary;

    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.68),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFE8DCCD)),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => isLogin = true),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: isLogin ? const Color(0xFF1E4B43) : Colors.transparent,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  'Entrar',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: isLogin ? Colors.white : activeColor,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => isLogin = false),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: !isLogin
                      ? const Color(0xFF1E4B43)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  'Crear cuenta',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: !isLogin ? Colors.white : activeColor,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF7F3EC), Color(0xFFF0E5D8), Color(0xFFE8EFE8)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              final isCompactAuthLayout =
                  constraints.maxWidth < 390 || constraints.maxHeight < 760;
              final heroTitleSize = isCompactAuthLayout ? 34.0 : 38.0;
              final heroTitleHeight = isCompactAuthLayout ? 1.0 : 0.95;
              final heroBottomPadding = isCompactAuthLayout ? 32.0 : 28.0;
              final authCardTopSpacing = isCompactAuthLayout ? 20.0 : 14.0;

              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    minHeight: constraints.maxHeight - 44,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      StaggeredReveal(
                        order: 0,
                        child: Container(
                        clipBehavior: Clip.antiAlias,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(40),
                          gradient: const LinearGradient(
                            colors: [
                              Color(0xFF112B29),
                              Color(0xFF1E4B43),
                              Color(0xFF32685E),
                              Color(0xFFC78259),
                            ],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x22000000),
                              blurRadius: 30,
                              offset: Offset(0, 18),
                            ),
                          ],
                        ),
                        child: Stack(
                          children: [
                            Positioned(
                              top: -24,
                              right: -20,
                              child: Container(
                                width: 180,
                                height: 180,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: Colors.white.withValues(alpha: 0.08),
                                ),
                              ),
                            ),
                            Positioned(
                              bottom: -50,
                              left: -26,
                              child: Container(
                                width: 160,
                                height: 160,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: Colors.white.withValues(alpha: 0.06),
                                ),
                              ),
                            ),
                            Padding(
                              padding: EdgeInsets.fromLTRB(
                                24,
                                24,
                                24,
                                heroBottomPadding,
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    padding: const EdgeInsets.fromLTRB(
                                      8,
                                      8,
                                      18,
                                      8,
                                    ),
                                    decoration: BoxDecoration(
                                      color: Colors.white.withValues(
                                        alpha: 0.12,
                                      ),
                                      borderRadius: BorderRadius.circular(24),
                                      border: Border.all(
                                        color: Colors.white.withValues(
                                          alpha: 0.08,
                                        ),
                                      ),
                                    ),
                                    child: const HarmonyHubBrand(
                                      iconSize: 54,
                                      fontSize: 18,
                                      gap: 14,
                                      stackedWordmark: false,
                                      textColor: Colors.white,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  const SizedBox(height: 14),
                                  Text(
                                    '¡Bienvenido a Harmony Hub!',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: heroTitleSize,
                                      height: heroTitleHeight,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      ),
                      Padding(
                        padding: EdgeInsets.only(top: authCardTopSpacing),
                        child: StaggeredReveal(
                          order: 1,
                          child: Container(
                          padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.94),
                            borderRadius: BorderRadius.circular(34),
                            border: Border.all(color: const Color(0xFFE7DBCD)),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x16000000),
                                blurRadius: 24,
                                offset: Offset(0, 12),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _authToggle(context),
                              const SizedBox(height: 22),
                              EditorialSectionHeader(
                                eyebrow: isLogin ? 'ACCESO' : 'NUEVA CUENTA',
                                title: isLogin
                                    ? 'Vuelve a tu ritmo'
                                    : 'Empieza tu espacio',
                                subtitle: isLogin
                                    ? 'Entra para recuperar tu historial y seguir construyendo una experiencia musical más afinada.'
                                    : 'Crea tu cuenta y empieza a transformar tus check-ins en sesiones y playlists con intención.',
                              ),
                              const SizedBox(height: 20),
                              TextField(
                                controller: emailController,
                                keyboardType: TextInputType.emailAddress,
                                textInputAction: TextInputAction.next,
                                decoration: const InputDecoration(
                                  labelText: 'Correo electrónico',
                                  hintText: 'tuemail@ejemplo.com',
                                  prefixIcon: Icon(Icons.mail_outline_rounded),
                                ),
                              ),
                              const SizedBox(height: 16),
                              TextField(
                                controller: passwordController,
                                obscureText: obscurePassword,
                                textInputAction: TextInputAction.done,
                                onSubmitted: (_) => loading ? null : submit(),
                                decoration: InputDecoration(
                                  labelText: 'Contraseña',
                                  prefixIcon: const Icon(
                                    Icons.lock_outline_rounded,
                                  ),
                                  suffixIcon: IconButton(
                                    onPressed: () {
                                      HapticFeedback.selectionClick();
                                      setState(() {
                                        obscurePassword = !obscurePassword;
                                      });
                                    },
                                    icon: Icon(
                                      obscurePassword
                                          ? Icons.visibility_outlined
                                          : Icons.visibility_off_outlined,
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 10),
                              Align(
                                alignment: Alignment.centerRight,
                                child: TextButton(
                                  onPressed: () {
                                    HapticFeedback.selectionClick();
                                    _resetPassword();
                                  },
                                  child: const Text('Olvidé mi contraseña'),
                                ),
                              ),
                              const SizedBox(height: 8),
                              FilledButton(
                                onPressed: loading ? null : submit,
                                child: loading
                                    ? const SizedBox(
                                        width: 22,
                                        height: 22,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          color: Colors.white,
                                        ),
                                      )
                                    : Text(
                                        isLogin
                                            ? 'Iniciar sesión'
                                            : 'Crear cuenta',
                                      ),
                              ),
                              const SizedBox(height: 18),
                              Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFF7F0E6),
                                  borderRadius: BorderRadius.circular(22),
                                  border: Border.all(
                                    color: const Color(0xFFE8DCCD),
                                  ),
                                ),
                                child: const Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Icon(
                                      Icons.shield_outlined,
                                      color: Color(0xFF1E4B43),
                                      size: 20,
                                    ),
                                    SizedBox(width: 12),
                                    Expanded(
                                      child: Text(
                                        'Tu acceso mantiene el tono íntimo de la app: menos fricción, más claridad y una entrada que no se siente técnica.',
                                        style: TextStyle(
                                          color: Color(0xFF5E645F),
                                          height: 1.45,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
