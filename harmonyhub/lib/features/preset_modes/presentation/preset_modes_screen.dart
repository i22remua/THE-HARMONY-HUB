import 'package:flutter/material.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:harmonyhub/features/preset_modes/data/preset_modes_repository.dart';
import 'package:harmonyhub/features/preset_modes/data/saved_preset_modes_firestore_service.dart';
import 'package:harmonyhub/features/preset_modes/domain/preset_mode.dart';
import 'package:harmonyhub/features/preset_modes/presentation/preset_mode_detail_screen.dart';
import 'package:harmonyhub/features/preset_modes/presentation/widgets/preset_mode_card.dart';

class PresetModesScreen extends StatefulWidget {
  const PresetModesScreen({super.key});

  @override
  State<PresetModesScreen> createState() => _PresetModesScreenState();
}

class _PresetModesScreenState extends State<PresetModesScreen> {
  final PresetModesRepository _repository = const PresetModesRepository();
  final SavedPresetModesFirestoreService _savedService =
      SavedPresetModesFirestoreService();
  Set<String> _savedModeIds = <String>{};
  bool _loadingSavedModes = true;

  @override
  void initState() {
    super.initState();
    _loadSavedModes();
  }

  Future<void> _loadSavedModes() async {
    try {
      final savedIds = await _savedService.getMySavedModeIds();
      if (!mounted) return;
      setState(() {
        _savedModeIds = savedIds;
        _loadingSavedModes = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loadingSavedModes = false);
    }
  }

  Future<void> _openSpotify(BuildContext context, PresetMode mode) async {
    final uri = Uri.parse(mode.spotifyPlaylistUrl);

    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
      return;
    }

    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('No se pudo abrir la playlist "${mode.title}".')),
    );
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _useAsTemplate(BuildContext context, PresetMode mode) async {
    final isSaved = _savedModeIds.contains(mode.id);

    try {
      if (isSaved) {
        await _savedService.removeMode(mode);
      } else {
        await _savedService.saveMode(mode);
      }

      if (!mounted) return;
      setState(() {
        if (isSaved) {
          _savedModeIds.remove(mode.id);
        } else {
          _savedModeIds.add(mode.id);
        }
      });

      _showMessage(
        isSaved
            ? '"${mode.title}" ya no está guardada para más tarde.'
            : '"${mode.title}" se ha guardado para que la recuperes cuando quieras.',
      );
    } catch (e) {
      _showMessage('No pude guardar esta idea ahora mismo: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final modes = _repository.getModes();
    final relaxModes = modes
        .where((mode) => mode.goal == 'relajacion')
        .toList();
    final focusModes = modes.where((mode) => mode.goal == 'foco').toList();
    final energyModes = modes.where((mode) => mode.goal == 'energia').toList();
    final savedModes = modes
        .where((mode) => _savedModeIds.contains(mode.id))
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Modos preestablecidos'),
        actions: const [HomeShortcutButton()],
      ),
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF8F1E8), Color(0xFFF0E6D9), Color(0xFFE7EDE6)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 32),
          children: [
            if (_loadingSavedModes)
              const Padding(
                padding: EdgeInsets.only(bottom: 12),
                child: LinearProgressIndicator(),
              ),
            if (!_loadingSavedModes && savedModes.isNotEmpty) ...[
              Text(
                'Guardados para luego',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontSize: 28),
              ),
              const SizedBox(height: 10),
              ...savedModes.map(
                (mode) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: PresetModeCard(
                    mode: mode,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => PresetModeDetailScreen(mode: mode),
                        ),
                      );
                    },
                    onOpenSpotify: () => _openSpotify(context, mode),
                    onUseAsTemplate: () => _useAsTemplate(context, mode),
                    isSaved: true,
                  ),
                ),
              ),
              const SizedBox(height: 10),
            ],
            Text(
              'Concentración con intención',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontSize: 28),
            ),
            const SizedBox(height: 10),
            ...focusModes.map(
              (mode) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: PresetModeCard(
                  mode: mode,
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => PresetModeDetailScreen(mode: mode),
                      ),
                    );
                  },
                  onOpenSpotify: () => _openSpotify(context, mode),
                  onUseAsTemplate: () => _useAsTemplate(context, mode),
                  isSaved: _savedModeIds.contains(mode.id),
                ),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Pausas para bajar revoluciones',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontSize: 28),
            ),
            const SizedBox(height: 10),
            ...relaxModes.map(
              (mode) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: PresetModeCard(
                  mode: mode,
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => PresetModeDetailScreen(mode: mode),
                      ),
                    );
                  },
                  onOpenSpotify: () => _openSpotify(context, mode),
                  onUseAsTemplate: () => _useAsTemplate(context, mode),
                  isSaved: _savedModeIds.contains(mode.id),
                ),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Impulso suave cuando lo necesitas',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontSize: 28),
            ),
            const SizedBox(height: 10),
            ...energyModes.map(
              (mode) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: PresetModeCard(
                  mode: mode,
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => PresetModeDetailScreen(mode: mode),
                      ),
                    );
                  },
                  onOpenSpotify: () => _openSpotify(context, mode),
                  onUseAsTemplate: () => _useAsTemplate(context, mode),
                  isSaved: _savedModeIds.contains(mode.id),
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
