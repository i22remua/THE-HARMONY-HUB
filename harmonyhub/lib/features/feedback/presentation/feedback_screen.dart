import 'package:flutter/material.dart';

import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/features/checkin/presentation/checkin_screen.dart';
import 'package:harmonyhub/features/feedback/data/feedback_firestore_service.dart';
import 'package:harmonyhub/features/feedback/data/feedback_service.dart';
import 'package:harmonyhub/features/home/presentation/app_shell.dart';

/// Pantalla final de sesión. Recoge cómo ha ido la experiencia para que el
/// sistema pueda aprender de ella.
class FeedbackScreen extends StatefulWidget {
  final String recommendationId;
  final String recommendationTitle;

  const FeedbackScreen({
    super.key,
    required this.recommendationId,
    required this.recommendationTitle,
  });

  @override
  State<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen> {
  final FeedbackService _feedbackService = FeedbackService();
  final FeedbackFirestoreService _feedbackFirestoreService =
      FeedbackFirestoreService();
  final TextEditingController _commentController = TextEditingController();

  bool? _helpful;
  String? _effect;
  String? _postSessionState;
  bool _isSubmitting = false;

  // Nuevo: por defecto activado, pero el backend también puede decidir
  // automáticamente si esta sesión debe influir solo en sesión o en gusto estable.
  bool _useForTasteProfile = true;

  final List<_FeedbackOption> _postSessionOptions = const [
    _FeedbackOption(
      value: 'mas_tranquilo',
      label: 'Más tranquilo/a',
      subtitle: 'Siento menos tensión que antes.',
      icon: Icons.spa_outlined,
    ),
    _FeedbackOption(
      value: 'mas_centrado',
      label: 'Más centrado/a',
      subtitle: 'Tengo más claridad y orden mental.',
      icon: Icons.filter_center_focus_outlined,
    ),
    _FeedbackOption(
      value: 'mas_animado',
      label: 'Más animado/a',
      subtitle: 'Me noto con más impulso o energía.',
      icon: Icons.bolt_outlined,
    ),
    _FeedbackOption(
      value: 'mas_acompanado',
      label: 'Más acompañado/a',
      subtitle: 'Me he sentido sostenido/a o acompañado/a.',
      icon: Icons.favorite_outline,
    ),
    _FeedbackOption(
      value: 'igual',
      label: 'Igual que antes',
      subtitle: 'No he notado un cambio claro.',
      icon: Icons.horizontal_rule_outlined,
    ),
    _FeedbackOption(
      value: 'peor',
      label: 'Peor de lo que estaba',
      subtitle: 'La sesión no me ha sentado bien.',
      icon: Icons.warning_amber_outlined,
    ),
  ];

  final List<_FeedbackOption> _effectOptions = const [
    _FeedbackOption(
      value: 'mejoro',
      label: 'Mejoró',
      subtitle: 'En conjunto me dejó mejor.',
      icon: Icons.trending_up_outlined,
    ),
    _FeedbackOption(
      value: 'igual',
      label: 'Igual',
      subtitle: 'No cambió demasiado cómo me sentía.',
      icon: Icons.remove_outlined,
    ),
    _FeedbackOption(
      value: 'empeoro',
      label: 'Empeoró',
      subtitle: 'No me ayudó o me dejó peor.',
      icon: Icons.trending_down_outlined,
    ),
  ];

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    // Guarda el feedback en backend y en Firestore para cerrar el ciclo:
    // recomendación -> playlist -> valoración del usuario -> aprendizaje.
    if (_helpful == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Indica si la sesión te ayudó o no, aunque sea un poco.',
          ),
        ),
      );
      return;
    }

    if (_postSessionState == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Cuéntame primero cómo te ha dejado la sesión.'),
        ),
      );
      return;
    }

    if (_effect == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Selecciona el efecto general de la sesión.'),
        ),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      await _feedbackService.submitFeedback(
        recommendationId: widget.recommendationId,
        recommendationTitle: widget.recommendationTitle,
        helpful: _helpful!,
        effect: _effect!,
        postSessionState: _postSessionState!,
        comment: _commentController.text,
        useForTasteProfile: _useForTasteProfile,
        preferenceScope: _useForTasteProfile ? 'both' : 'session_only',
      );

      await _feedbackFirestoreService.saveFeedback(
        recommendationId: widget.recommendationId,
        recommendationTitle: widget.recommendationTitle,
        helpful: _helpful!,
        effect: _effect!,
        postSessionState: _postSessionState!,
        comment: _commentController.text,
        useForTasteProfile: _useForTasteProfile,
        preferenceScope: _useForTasteProfile ? 'both' : 'session_only',
      );

      if (!mounted) return;

      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const AppShell(initialIndex: 0)),
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('No he podido guardar lo que me has contado: $e'),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Widget _buildBooleanChoice({
    required String title,
    String? subtitle,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            if (subtitle != null) ...[
              const SizedBox(height: 6),
              Text(
                subtitle,
                style: TextStyle(color: Colors.grey.shade700, height: 1.3),
              ),
              const SizedBox(height: 14),
            ] else
              const SizedBox(height: 14),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                ChoiceChip(
                  label: const Text('Sí, me vino bien'),
                  selected: _helpful == true,
                  onSelected: (_) {
                    setState(() {
                      _helpful = true;
                    });
                  },
                ),
                ChoiceChip(
                  label: const Text('No demasiado'),
                  selected: _helpful == false,
                  onSelected: (_) {
                    setState(() {
                      _helpful = false;
                    });
                  },
                ),
                ChoiceChip(
                  label: const Text('Todavía no lo tengo claro'),
                  selected: _helpful == null,
                  onSelected: (_) {
                    setState(() {
                      _helpful = null;
                    });
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionSelector({
    required String title,
    String? subtitle,
    required String? selectedValue,
    required List<_FeedbackOption> options,
    required ValueChanged<String> onChanged,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            if (subtitle != null) ...[
              const SizedBox(height: 6),
              Text(
                subtitle,
                style: TextStyle(color: Colors.grey.shade700, height: 1.3),
              ),
              const SizedBox(height: 14),
            ] else
              const SizedBox(height: 14),
            ...options.map(
              (option) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: InkWell(
                  borderRadius: BorderRadius.circular(18),
                  onTap: () => onChanged(option.value),
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: selectedValue == option.value
                          ? const Color(0xFFF7EFE4)
                          : const Color(0xFFFFFCF8),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: selectedValue == option.value
                            ? Theme.of(context).colorScheme.primary
                            : Colors.grey.shade300,
                        width: selectedValue == option.value ? 1.8 : 1.0,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(option.icon),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                option.label,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                option.subtitle,
                                style: TextStyle(
                                  color: Colors.grey.shade700,
                                  height: 1.25,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        if (selectedValue == option.value)
                          Icon(
                            Icons.check_circle,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLearningPreferenceCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '¿Quieres que recuerde esta sesión para próximas veces?',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 14),
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: Text(
                _useForTasteProfile
                    ? 'Sí, me representa bastante'
                    : 'No, era algo más puntual',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              subtitle: Text(
                _useForTasteProfile
                    ? 'Podrá influir un poco más en futuras recomendaciones.'
                    : 'La tendré en cuenta como contexto de hoy, pero no como algo estable.',
              ),
              value: _useForTasteProfile,
              onChanged: (value) {
                setState(() {
                  _useForTasteProfile = value;
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCommentBox() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Si quieres, dime algo más',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _commentController,
              maxLines: 4,
              maxLength: 180,
              decoration: const InputDecoration(
                hintText:
                    'Por ejemplo: hoy necesitaba algo menos intenso, o me vino muy bien para centrarme.',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActions() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Acciones rápidas',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 14),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.of(context).pushAndRemoveUntil(
                      MaterialPageRoute(builder: (_) => const CheckinScreen()),
                      (route) => false,
                    );
                  },
                  icon: const Icon(Icons.refresh_rounded),
                  label: const Text('Volver a generar'),
                ),
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.of(context).pushAndRemoveUntil(
                      MaterialPageRoute(
                        builder: (_) => const AppShell(initialIndex: 1),
                      ),
                      (route) => false,
                    );
                  },
                  icon: const Icon(Icons.explore_outlined),
                  label: const Text('Explorar otra opción'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF8F1E8), Color(0xFFF1E7DA), Color(0xFFE8EFE8)],
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
                      '¿Qué tal te sentó?',
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
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(30),
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF12342F),
                      Color(0xFF1E4B43),
                      Color(0xFF3A7266),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x22000000),
                      blurRadius: 24,
                      offset: Offset(0, 12),
                    ),
                  ],
                ),
                child: Stack(
                  children: [
                    Positioned(
                      top: -10,
                      right: -10,
                      child: Container(
                        width: 104,
                        height: 104,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.12),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 7,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.3),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: const Text(
                            'CIERRE DE SESIÓN',
                            style: TextStyle(
                              color: Colors.white,
                              letterSpacing: 1.5,
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Antes de cerrar, me ayudaría saber cómo te ha dejado esta sesión.',
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(
                                height: 1.0,
                                fontSize: 34,
                                color: Colors.white,
                              ),
                        ),
                        const SizedBox(height: 10),
                        const Text(
                          'No hace falta una respuesta perfecta. Solo una impresión breve y honesta para seguir afinando mejor contigo.',
                          style: TextStyle(
                            height: 1.45,
                            color: Color(0xFFE7F2ED),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              _buildOptionSelector(
                title: '¿Cómo te ha dejado esta sesión?',
                selectedValue: _postSessionState,
                options: _postSessionOptions,
                onChanged: (value) {
                  setState(() {
                    _postSessionState = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildBooleanChoice(
                title: 'En conjunto, ¿te vino bien?',
              ),
              const SizedBox(height: 12),
              _buildOptionSelector(
                title: '¿Qué balance haces de la sesión?',
                selectedValue: _effect,
                options: _effectOptions,
                onChanged: (value) {
                  setState(() {
                    _effect = value;
                  });
                },
              ),
              const SizedBox(height: 12),
              _buildLearningPreferenceCard(),
              const SizedBox(height: 12),
              _buildCommentBox(),
              const SizedBox(height: 12),
              _buildQuickActions(),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _isSubmitting ? null : _submit,
                child: _isSubmitting
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('Guardar cómo me fue'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FeedbackOption {
  final String value;
  final String label;
  final String subtitle;
  final IconData icon;

  const _FeedbackOption({
    required this.value,
    required this.label,
    required this.subtitle,
    required this.icon,
  });
}
