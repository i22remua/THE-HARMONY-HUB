import 'package:flutter/material.dart';
import 'package:harmonyhub/features/preset_modes/domain/preset_mode.dart';

class PresetModeCard extends StatelessWidget {
  final PresetMode mode;
  final VoidCallback? onTap;
  final VoidCallback onOpenSpotify;
  final VoidCallback? onUseAsTemplate;
  final bool isSaved;

  const PresetModeCard({
    super.key,
    required this.mode,
    this.onTap,
    required this.onOpenSpotify,
    this.onUseAsTemplate,
    this.isSaved = false,
  });

  List<Color> _colorsForGoal() {
    switch (mode.goal) {
      case 'relajacion':
        return const [Color(0xFF567565), Color(0xFF86A18F), Color(0xFFE7DDD0)];
      case 'energia':
        return const [Color(0xFFB56A48), Color(0xFFD68D69), Color(0xFFF0E0D3)];
      case 'foco':
      default:
        return const [Color(0xFF355E66), Color(0xFF57808A), Color(0xFFE3E5E8)];
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = _colorsForGoal();

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(24),
                  gradient: LinearGradient(
                    colors: colors,
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 54,
                          height: 54,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.18),
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: Icon(mode.icon, size: 28, color: Colors.white),
                        ),
                        const Spacer(),
                        if (isSaved)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.18),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: const Text(
                              'Guardada',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w700,
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 18),
                    Text(
                      mode.title,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      mode.subtitle,
                      style: const TextStyle(
                        color: Color(0xFFF7F4EF),
                        fontWeight: FontWeight.w600,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  FilledButton.icon(
                    onPressed: onOpenSpotify,
                    icon: const Icon(Icons.open_in_new),
                    label: const Text('Abrir en Spotify'),
                  ),
                  if (onUseAsTemplate != null)
                    OutlinedButton.icon(
                      onPressed: onUseAsTemplate,
                      icon: Icon(
                        isSaved
                            ? Icons.bookmark_added_outlined
                            : Icons.bookmark_add_outlined,
                      ),
                      label: Text(
                        isSaved ? 'Guardada para luego' : 'Guardar para luego',
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
