import 'package:flutter/material.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:harmonyhub/features/preset_modes/data/saved_preset_modes_firestore_service.dart';
import 'package:harmonyhub/features/preset_modes/domain/preset_mode.dart';

class PresetModeDetailScreen extends StatefulWidget {
  final PresetMode mode;

  const PresetModeDetailScreen({super.key, required this.mode});

  @override
  State<PresetModeDetailScreen> createState() => _PresetModeDetailScreenState();
}

class _PresetModeDetailScreenState extends State<PresetModeDetailScreen> {
  final SavedPresetModesFirestoreService _savedService =
      SavedPresetModesFirestoreService();
  bool _saved = false;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    final ids = await _savedService.getMySavedModeIds();
    if (!mounted) return;
    setState(() {
      _saved = ids.contains(widget.mode.id);
      _loading = false;
    });
  }

  Future<void> _toggleSaved() async {
    if (_saved) {
      await _savedService.removeMode(widget.mode);
    } else {
      await _savedService.saveMode(widget.mode);
    }

    if (!mounted) return;
    setState(() {
      _saved = !_saved;
    });
  }

  Future<void> _openSpotify() async {
    final uri = Uri.parse(widget.mode.spotifyPlaylistUrl);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Widget _detailChip({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white, size: 18),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: Color(0xFFF4F1EC),
                  fontSize: 10,
                  letterSpacing: 1.2,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                value,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
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
            colors: [Color(0xFFF7F3EC), Color(0xFFF1E6D8), Color(0xFFE8EFE8)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 120),
            children: [
              Row(
                children: [
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.82),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: IconButton(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.arrow_back_rounded),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Text(
                      'Modo guiado',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF1F2421),
                      ),
                    ),
                  ),
                  const HomeShortcutButton(),
                ],
              ),
              const SizedBox(height: 18),
              Container(
                clipBehavior: Clip.antiAlias,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(40),
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFFB96E4B),
                      Color(0xFFD6946E),
                      Color(0xFFEDD6C4),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x22000000),
                      blurRadius: 28,
                      offset: Offset(0, 16),
                    ),
                  ],
                ),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 60,
                        height: 60,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.18),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Icon(
                          widget.mode.icon,
                          color: const Color(0xFF1F2421),
                        ),
                      ),
                      const SizedBox(height: 22),
                      const Text(
                        'ATAJO MUSICAL',
                        style: TextStyle(
                          fontSize: 11,
                          letterSpacing: 1.7,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF1F2421),
                        ),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        widget.mode.title,
                        style: Theme.of(context).textTheme.headlineLarge
                            ?.copyWith(
                              fontSize: 44,
                              height: 0.9,
                              color: const Color(0xFF1F2421),
                            ),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        widget.mode.subtitle,
                        style: const TextStyle(
                          color: Color(0xFF2B2F2D),
                          height: 1.45,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 18),
                      Wrap(
                        spacing: 10,
                        runSpacing: 10,
                        children: [
                          _detailChip(
                            icon: Icons.flag_outlined,
                            label: 'OBJETIVO',
                            value: widget.mode.goal,
                          ),
                          _detailChip(
                            icon: Icons.favorite_outline_rounded,
                            label: 'MOMENTO',
                            value: widget.mode.suggestedMood,
                          ),
                          _detailChip(
                            icon: Icons.north_east_rounded,
                            label: 'SALIDA',
                            value: widget.mode.suggestedOutcome,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              Container(
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  color: const Color(0xFF173734),
                  borderRadius: BorderRadius.circular(32),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x22000000),
                      blurRadius: 24,
                      offset: Offset(0, 14),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'ACCIONES',
                      style: TextStyle(
                        color: Color(0xFFDDE6DE),
                        fontSize: 11,
                        letterSpacing: 1.7,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 18),
                    FilledButton.icon(
                      onPressed: _openSpotify,
                      icon: const Icon(Icons.open_in_new_rounded),
                      label: const Text('Abrir en Spotify'),
                    ),
                    const SizedBox(height: 10),
                    OutlinedButton.icon(
                      onPressed: _loading ? null : _toggleSaved,
                      icon: Icon(
                        _saved
                            ? Icons.bookmark_added_outlined
                            : Icons.bookmark_add_outlined,
                      ),
                      label: Text(
                        _saved ? 'Guardado para luego' : 'Guardar para luego',
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
