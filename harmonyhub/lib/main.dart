import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:harmonyhub/features/auth/presentation/login_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const HarmonyHubApp());
}

class HarmonyHubApp extends StatelessWidget {
  const HarmonyHubApp({super.key});

  @override
  Widget build(BuildContext context) {
    const porcelain = Color(0xFFF7F3EC);
    const mist = Color(0xFFE8EFE8);
    const forestInk = Color(0xFF1E4B43);
    const clayGold = Color(0xFFC8845A);
    const softSand = Color(0xFFE8D8C7);
    const graphite = Color(0xFF1F2421);
    const fogText = Color(0xFF66706A);
    const line = Color(0xFFE6DACD);

    final base = ThemeData(useMaterial3: true);
    final appText = GoogleFonts.plusJakartaSansTextTheme(
      base.textTheme,
    ).apply(bodyColor: graphite, displayColor: graphite);

    final textTheme = appText.copyWith(
      headlineLarge: appText.headlineLarge?.copyWith(
        fontSize: 40,
        height: 0.98,
        fontWeight: FontWeight.w800,
        letterSpacing: -1.4,
      ),
      headlineMedium: appText.headlineMedium?.copyWith(
        fontSize: 32,
        height: 1.0,
        fontWeight: FontWeight.w800,
        letterSpacing: -1.0,
      ),
      headlineSmall: appText.headlineSmall?.copyWith(
        fontSize: 26,
        height: 1.08,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.7,
      ),
      titleLarge: appText.titleLarge?.copyWith(
        fontSize: 24,
        height: 1.12,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.7,
      ),
      titleMedium: appText.titleMedium?.copyWith(
        fontSize: 18,
        height: 1.2,
        fontWeight: FontWeight.w700,
      ),
      bodyLarge: appText.bodyLarge?.copyWith(
        fontSize: 16,
        height: 1.55,
        fontWeight: FontWeight.w500,
        color: graphite,
      ),
      bodyMedium: appText.bodyMedium?.copyWith(
        fontSize: 14.5,
        height: 1.5,
        fontWeight: FontWeight.w500,
        color: fogText,
      ),
      labelLarge: appText.labelLarge?.copyWith(
        fontSize: 15,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.1,
      ),
    );

    final lightTheme = ThemeData(
      useMaterial3: true,
      fontFamily: GoogleFonts.plusJakartaSans().fontFamily,
      colorScheme: const ColorScheme(
        brightness: Brightness.light,
        primary: forestInk,
        onPrimary: Colors.white,
        secondary: clayGold,
        onSecondary: Colors.white,
        error: Color(0xFFB3261E),
        onError: Colors.white,
        surface: Color(0xFFFFFCF8),
        onSurface: graphite,
        primaryContainer: Color(0xFFDCEAE4),
        onPrimaryContainer: forestInk,
        secondaryContainer: Color(0xFFF0D8C8),
        onSecondaryContainer: graphite,
        tertiary: Color(0xFF9DB8AD),
        onTertiary: graphite,
        tertiaryContainer: mist,
        onTertiaryContainer: graphite,
        surfaceContainer: porcelain,
        surfaceContainerHighest: softSand,
        onSurfaceVariant: fogText,
        outline: line,
        outlineVariant: Color(0xFFF0E6DA),
        shadow: Color(0x121F2421),
        scrim: Color(0x661F2421),
        inverseSurface: forestInk,
        onInverseSurface: Colors.white,
        inversePrimary: Color(0xFFA5CDC0),
      ),
      scaffoldBackgroundColor: porcelain,
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        centerTitle: false,
        elevation: 0,
        backgroundColor: Colors.transparent,
        foregroundColor: graphite,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: textTheme.headlineSmall?.copyWith(
          fontSize: 22,
          color: graphite,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: const Color(0xFFFFFCF8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(30),
          side: const BorderSide(color: line),
        ),
        margin: EdgeInsets.zero,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFFFFCF8),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 18,
          vertical: 18,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(color: line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(color: line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(24),
          borderSide: const BorderSide(width: 1.6, color: forestInk),
        ),
        hintStyle: textTheme.bodyMedium?.copyWith(color: fogText),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size.fromHeight(58),
          elevation: 0,
          backgroundColor: forestInk,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(22),
          ),
          textStyle: textTheme.labelLarge,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(58),
          elevation: 0,
          backgroundColor: forestInk,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(22),
          ),
          textStyle: textTheme.labelLarge,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(56),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(22),
          ),
          foregroundColor: forestInk,
          side: const BorderSide(color: line),
          backgroundColor: const Color(0xFFFFFCF8),
          textStyle: textTheme.labelLarge,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: forestInk,
          textStyle: textTheme.labelLarge?.copyWith(fontSize: 14.5),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: const Color(0xFFFFF8F0),
        selectedColor: softSand,
        side: const BorderSide(color: line),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        labelStyle: textTheme.bodyMedium?.copyWith(
          fontWeight: FontWeight.w700,
          color: graphite,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: Color(0xFFFFFCF8),
        surfaceTintColor: Colors.transparent,
      ),
      listTileTheme: const ListTileThemeData(
        contentPadding: EdgeInsets.symmetric(horizontal: 18, vertical: 6),
        iconColor: forestInk,
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          foregroundColor: forestInk,
          backgroundColor: Colors.white.withValues(alpha: 0.78),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (states) =>
              states.contains(WidgetState.selected) ? Colors.white : porcelain,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? forestInk
              : const Color(0xFFDCCFBE),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: forestInk,
        contentTextStyle: const TextStyle(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      ),
      navigationBarTheme: NavigationBarThemeData(
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => textTheme.bodyMedium?.copyWith(
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w800
                : FontWeight.w600,
            color: states.contains(WidgetState.selected) ? forestInk : fogText,
          ),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            size: 24,
            color: states.contains(WidgetState.selected) ? forestInk : fogText,
          ),
        ),
        backgroundColor: const Color(0xFFF8F3EB),
        indicatorColor: const Color(0xFFEFD4C3),
        height: 78,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
      ),
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.android: FadeForwardsPageTransitionsBuilder(),
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.macOS: CupertinoPageTransitionsBuilder(),
          TargetPlatform.linux: FadeForwardsPageTransitionsBuilder(),
          TargetPlatform.windows: FadeForwardsPageTransitionsBuilder(),
        },
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: forestInk,
        circularTrackColor: Color(0xFFE6DACB),
        linearTrackColor: Color(0xFFE6DACB),
      ),
      dividerColor: line,
    );

    return MaterialApp(
      title: 'Harmony Hub',
      debugShowCheckedModeBanner: false,
      theme: lightTheme,
      home: const LoginScreen(),
    );
  }
}
