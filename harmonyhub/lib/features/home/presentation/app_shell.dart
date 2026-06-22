import 'package:flutter/material.dart';
import 'package:harmonyhub/features/history/presentation/history_screen.dart';
import 'package:harmonyhub/features/home/presentation/home_screen.dart';
import 'package:harmonyhub/features/preset_modes/presentation/preset_modes_screen.dart';
import 'package:harmonyhub/features/profile/presentation/profile_screen.dart';
import 'package:harmonyhub/features/profile/presentation/user_learning_screen.dart';

class AppShell extends StatefulWidget {
  final int initialIndex;

  const AppShell({super.key, this.initialIndex = 0});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  late int _index;

  final List<Widget> _pages = const [
    HomeScreen(),
    PresetModesScreen(),
    HistoryScreen(),
    UserLearningScreen(),
    ProfileScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex;
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final isCompactBottomNav = width < 410;
    final theme = Theme.of(context);

    return Scaffold(
      extendBody: true,
      body: IndexedStack(index: _index, children: _pages),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        child: Container(
          padding: EdgeInsets.fromLTRB(
            isCompactBottomNav ? 8 : 10,
            10,
            isCompactBottomNav ? 8 : 10,
            8,
          ),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                const Color(0xFFFFFCF8).withValues(alpha: 0.96),
                const Color(0xFFF7F0E6).withValues(alpha: 0.96),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(34),
            border: Border.all(color: const Color(0xFFE8DCCD)),
            boxShadow: const [
              BoxShadow(
                color: Color(0x141F2421),
                blurRadius: 28,
                offset: Offset(0, 14),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(28),
            child: NavigationBarTheme(
              data: NavigationBarThemeData(
                labelTextStyle: WidgetStateProperty.resolveWith(
                  (states) =>
                      (isCompactBottomNav
                              ? theme.textTheme.labelSmall
                              : theme.textTheme.bodyMedium)
                          ?.copyWith(
                            fontSize: isCompactBottomNav ? 10.5 : null,
                            fontWeight: states.contains(WidgetState.selected)
                                ? FontWeight.w800
                                : FontWeight.w600,
                            color: states.contains(WidgetState.selected)
                                ? const Color(0xFF1F2F2B)
                                : const Color(0xFF7A756E),
                          ),
                ),
                iconTheme: WidgetStateProperty.resolveWith(
                  (states) => IconThemeData(
                    size: isCompactBottomNav ? 22 : 24,
                    color: states.contains(WidgetState.selected)
                        ? const Color(0xFF1F2F2B)
                        : const Color(0xFF7A756E),
                  ),
                ),
                height: isCompactBottomNav ? 74 : 78,
              ),
              child: NavigationBar(
                backgroundColor: Colors.transparent,
                selectedIndex: _index,
                onDestinationSelected: (value) {
                  setState(() {
                    _index = value;
                  });
                },
                destinations: const [
                  NavigationDestination(
                    icon: Icon(Icons.home_outlined),
                    selectedIcon: Icon(Icons.home_rounded),
                    label: 'Home',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.auto_awesome_outlined),
                    selectedIcon: Icon(Icons.auto_awesome),
                    label: 'Modos',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.history_rounded),
                    selectedIcon: Icon(Icons.history_toggle_off_rounded),
                    label: 'Historial',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.psychology_alt_outlined),
                    selectedIcon: Icon(Icons.psychology_alt_rounded),
                    label: 'Aprendizaje',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.person_outline_rounded),
                    selectedIcon: Icon(Icons.person_rounded),
                    label: 'Perfil',
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
