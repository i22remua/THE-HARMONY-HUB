import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:harmonyhub/features/history/data/history_firestore_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final HistoryFirestoreService _service = HistoryFirestoreService();
  static const int _historyPageSize = 12;

  List<Map<String, dynamic>> checkins = [];
  List<Map<String, dynamic>> recommendations = [];
  List<Map<String, dynamic>> feedbackList = [];
  List<Map<String, dynamic>> generatedPlaylists = [];
  HistoryTotals? totals;
  bool loading = true;
  bool _loadingMoreCheckins = false;
  bool _loadingMoreRecommendations = false;
  bool _loadingMoreFeedback = false;
  bool _loadingMorePlaylists = false;
  bool _hasMoreCheckins = true;
  bool _hasMoreRecommendations = true;
  bool _hasMoreFeedback = true;
  bool _hasMorePlaylists = true;
  dynamic _checkinsCursor;
  dynamic _recommendationsCursor;
  dynamic _feedbackCursor;
  dynamic _playlistsCursor;
  String _viewFilter = 'todo';
  String _emotionFilter = 'todas';
  String _goalFilter = 'todos';
  int _daysFilter = 0;

  @override
  void initState() {
    super.initState();
    loadHistory();
  }

  Future<void> loadHistory() async {
    // El historial se reconstruye desde cuatro colecciones distintas para poder
    // enseñar el ciclo completo de uso: check-in, recomendación, playlist y
    // feedback. La actividad se carga por lotes para no disparar lecturas.
    setState(() {
      loading = true;
      totals = null;
      _loadingMoreCheckins = false;
      _loadingMoreRecommendations = false;
      _loadingMoreFeedback = false;
      _loadingMorePlaylists = false;
    });

    try {
      final results = await Future.wait([
        _service.getMyCheckinsPage(limit: _historyPageSize),
        _service.getMyRecommendationsPage(limit: _historyPageSize),
        _service.getMyFeedbackPage(limit: _historyPageSize),
        _service.getMyGeneratedPlaylistsPage(limit: _historyPageSize),
      ]);

      if (!mounted) return;
      setState(() {
        checkins = results[0].items;
        recommendations = results[1].items;
        feedbackList = results[2].items;
        generatedPlaylists = results[3].items;
        _checkinsCursor = results[0].cursor;
        _recommendationsCursor = results[1].cursor;
        _feedbackCursor = results[2].cursor;
        _playlistsCursor = results[3].cursor;
        _hasMoreCheckins = results[0].hasMore;
        _hasMoreRecommendations = results[1].hasMore;
        _hasMoreFeedback = results[2].hasMore;
        _hasMorePlaylists = results[3].hasMore;
        loading = false;
      });

      try {
        final loadedTotals = await _service.getMyHistoryTotals();
        if (!mounted) return;
        setState(() {
          totals = loadedTotals;
        });
      } catch (_) {
        // Si el agregado falla por reglas, cuota o compatibilidad, mantenemos
        // igualmente la muestra reciente cargada y dejamos la cabecera en modo
        // fallback con los datos visibles.
      }
    } catch (e) {
      setState(() => loading = false);

      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error cargando historial: $e')));
    }
  }

  Future<void> _loadMoreCheckins() async {
    if (_loadingMoreCheckins || !_hasMoreCheckins) return;

    setState(() => _loadingMoreCheckins = true);
    try {
      final page = await _service.getMyCheckinsPage(
        limit: _historyPageSize,
        startAfterCreatedAt: _checkinsCursor,
      );

      if (!mounted) return;
      setState(() {
        checkins = [...checkins, ...page.items];
        _checkinsCursor = page.cursor;
        _hasMoreCheckins = page.hasMore;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No se pudieron cargar más check-ins: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => _loadingMoreCheckins = false);
      }
    }
  }

  Future<void> _loadMoreRecommendations() async {
    if (_loadingMoreRecommendations || !_hasMoreRecommendations) return;

    setState(() => _loadingMoreRecommendations = true);
    try {
      final page = await _service.getMyRecommendationsPage(
        limit: _historyPageSize,
        startAfterCreatedAt: _recommendationsCursor,
      );

      if (!mounted) return;
      setState(() {
        recommendations = [...recommendations, ...page.items];
        _recommendationsCursor = page.cursor;
        _hasMoreRecommendations = page.hasMore;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('No se pudieron cargar más recomendaciones: $e'),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _loadingMoreRecommendations = false);
      }
    }
  }

  Future<void> _loadMorePlaylists() async {
    if (_loadingMorePlaylists || !_hasMorePlaylists) return;

    setState(() => _loadingMorePlaylists = true);
    try {
      final page = await _service.getMyGeneratedPlaylistsPage(
        limit: _historyPageSize,
        startAfterCreatedAt: _playlistsCursor,
      );

      if (!mounted) return;
      setState(() {
        generatedPlaylists = [...generatedPlaylists, ...page.items];
        _playlistsCursor = page.cursor;
        _hasMorePlaylists = page.hasMore;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No se pudieron cargar más playlists: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => _loadingMorePlaylists = false);
      }
    }
  }

  Future<void> _loadMoreFeedback() async {
    if (_loadingMoreFeedback || !_hasMoreFeedback) return;

    setState(() => _loadingMoreFeedback = true);
    try {
      final page = await _service.getMyFeedbackPage(
        limit: _historyPageSize,
        startAfterCreatedAt: _feedbackCursor,
      );

      if (!mounted) return;
      setState(() {
        feedbackList = [...feedbackList, ...page.items];
        _feedbackCursor = page.cursor;
        _hasMoreFeedback = page.hasMore;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No se pudo cargar más feedback: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => _loadingMoreFeedback = false);
      }
    }
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 22, bottom: 10),
      child: EditorialSectionHeader(eyebrow: 'SECCION', title: title),
    );
  }

  Future<void> _openUrl(String? url) async {
    if (url == null || url.isEmpty) return;

    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se pudo abrir la playlist')),
      );
    }
  }

  DateTime? _asDateTime(dynamic value) {
    if (value == null) return null;

    if (value is Timestamp) {
      return value.toDate();
    }

    if (value is DateTime) {
      return value;
    }

    if (value is String) {
      return DateTime.tryParse(value);
    }

    if (value is int) {
      return DateTime.fromMillisecondsSinceEpoch(value);
    }

    return null;
  }

  String _twoDigits(int value) => value.toString().padLeft(2, '0');

  String _formatDateTime(dynamic value) {
    final date = _asDateTime(value);
    if (date == null) return '-';

    final day = _twoDigits(date.day);
    final month = _twoDigits(date.month);
    final year = date.year;
    final hour = _twoDigits(date.hour);
    final minute = _twoDigits(date.minute);

    return '$day/$month/$year · $hour:$minute';
  }

  String _boolLabel(dynamic value) {
    if (value == true) return 'Sí';
    if (value == false) return 'No';
    return '-';
  }

  bool _matchesDateFilter(dynamic value) {
    if (_daysFilter == 0) return true;
    final date = _asDateTime(value);
    if (date == null) return false;
    final threshold = DateTime.now().subtract(Duration(days: _daysFilter));
    return date.isAfter(threshold);
  }

  bool _matchesEmotion(Map<String, dynamic> item) {
    if (_emotionFilter == 'todas') return true;
    return item['mood']?.toString().toLowerCase() == _emotionFilter;
  }

  bool _matchesGoal(Map<String, dynamic> item) {
    if (_goalFilter == 'todos') return true;
    return item['goal']?.toString().toLowerCase() == _goalFilter;
  }

  Widget _filterChip({
    required String label,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) {
        HapticFeedback.selectionClick();
        onTap();
      },
    );
  }

  String _effectLabel(String? value) {
    switch (value) {
      case 'mejoro':
        return 'Mejoró';
      case 'igual':
        return 'Igual';
      case 'empeoro':
        return 'Empeoró';
      default:
        return value ?? '-';
    }
  }

  String _postSessionLabel(String? value) {
    switch (value) {
      case 'mas_tranquilo':
        return 'Más tranquilo/a';
      case 'mas_centrado':
        return 'Más centrado/a';
      case 'mas_animado':
        return 'Más animado/a';
      case 'mas_acompanado':
        return 'Más acompañado/a';
      case 'igual':
        return 'Igual que antes';
      case 'peor':
        return 'Peor';
      default:
        return value ?? '-';
    }
  }

  String _goalLabel(String? value) {
    switch ((value ?? '').toLowerCase()) {
      case 'energia':
        return 'Energía';
      case 'foco':
        return 'Foco';
      case 'relajacion':
        return 'Relajación';
      default:
        return value == null || value.isEmpty ? '-' : value;
    }
  }

  String _energyLabel(String? value) {
    switch ((value ?? '').toLowerCase()) {
      case 'baja':
        return 'suave';
      case 'media':
        return 'equilibrada';
      case 'media-alta':
        return 'con buen impulso';
      case 'alta':
        return 'alta';
      default:
        return value == null || value.isEmpty ? '-' : value;
    }
  }

  String _valenceLabel(String? value) {
    switch ((value ?? '').toLowerCase()) {
      case 'positiva':
        return 'luminoso';
      case 'neutral':
        return 'estable';
      case 'calmada':
        return 'sereno';
      default:
        return value == null || value.isEmpty ? '-' : value;
    }
  }

  String _moodLabel(String? value) {
    switch ((value ?? '').toLowerCase()) {
      case 'neutral':
        return 'Neutral';
      case 'estresado':
        return 'Estresado/a';
      case 'triste':
        return 'Triste';
      case 'cansado':
        return 'Cansado/a';
      case 'feliz':
        return 'Feliz';
      default:
        return value == null || value.isEmpty ? '-' : value;
    }
  }

  String _noiseLabel(String? value) {
    switch ((value ?? '').toLowerCase()) {
      case 'quiet':
        return 'Silencio estable';
      case 'moderate':
        return 'Ruido moderado';
      case 'active':
        return 'Entorno activo';
      case 'loud':
        return 'Ruido intenso';
      default:
        return value == null || value.isEmpty ? 'Sin entorno' : value;
    }
  }

  String _outcomeLabel(String? value) {
    switch ((value ?? '').toLowerCase()) {
      case 'mas_centrado':
        return 'Más centrado';
      case 'mas_calmado':
        return 'Más calmado';
      case 'mas_despierto':
        return 'Más despierto';
      case 'mas_acompanado':
        return 'Más acompañado';
      default:
        return value == null || value.isEmpty
            ? '-'
            : value.replaceAll('_', ' ');
    }
  }

  Widget _buildDateText(dynamic createdAt) {
    return Text(
      'Fecha: ${_formatDateTime(createdAt)}',
      style: TextStyle(color: Colors.grey.shade700, fontSize: 12.5),
    );
  }

  Widget _summaryStat({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Expanded(
      child: EditorialPanel(
        radius: 24,
        padding: const EdgeInsets.all(16),
        accentColor: const Color(0xFF1E4B43),
        child: Column(
          children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: const Color(0xFFE9F0EB),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: const Color(0xFF204F46)),
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Color(0xFF5E645F)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _recordCard({
    required IconData icon,
    required String title,
    required dynamic createdAt,
    required List<Widget> pills,
    String? body,
    VoidCallback? onTap,
    Widget? trailing,
  }) {
    return EditorialPanel(
      radius: 28,
      padding: const EdgeInsets.all(16),
      accentColor: const Color(0xFFC8845A),
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: const Color(0xFFE9F0EB),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(icon, color: const Color(0xFF204F46)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 17,
                    ),
                  ),
                ),
                ...[trailing].whereType<Widget>(),
              ],
            ),
            const SizedBox(height: 10),
            _buildDateText(createdAt),
            const SizedBox(height: 10),
            Wrap(spacing: 8, runSpacing: 8, children: pills),
            if (body != null && body.trim().isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                body,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: Color(0xFF5E645F), height: 1.4),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _infoPill({required String label, IconData? icon}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFCF8),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFE7DBCD)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 15, color: const Color(0xFF5E645F)),
            const SizedBox(width: 6),
          ],
          Text(
            label,
            style: const TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w600,
              color: Color(0xFF5E645F),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeedbackCard(Map<String, dynamic> item) {
    final comment = item['comment']?.toString();

    return _recordCard(
      icon: Icons.rate_review_outlined,
      title: item['recommendation_title'] ?? 'Feedback',
      createdAt: item['created_at'],
      body: comment == null || comment.trim().isEmpty
          ? null
          : 'Mensaje: $comment',
      pills: [
        _infoPill(
          label: 'Helpful ${_boolLabel(item['helpful'])}',
          icon: Icons.thumb_up_alt_outlined,
        ),
        _infoPill(
          label: _effectLabel(item['effect']?.toString()),
          icon: Icons.auto_graph_outlined,
        ),
        _infoPill(
          label: _postSessionLabel(item['post_session_state']?.toString()),
          icon: Icons.favorite_outline,
        ),
      ],
    );
  }

  Widget _buildCheckinCard(Map<String, dynamic> item) {
    return _recordCard(
      icon: Icons.favorite_outline,
      title:
          '${_goalLabel(item['goal']?.toString())} · ${_moodLabel(item['mood']?.toString())}',
      createdAt: item['created_at'],
      pills: [
        _infoPill(
          label: _goalLabel(item['goal']?.toString()),
          icon: Icons.flag_outlined,
        ),
        _infoPill(
          label: _moodLabel(item['mood']?.toString()),
          icon: Icons.mood_outlined,
        ),
        _infoPill(
          label: 'Estrés ${item['stress_level']}/5',
          icon: Icons.speed_outlined,
        ),
        _infoPill(
          label: 'Energía ${item['energy_level']}/5',
          icon: Icons.bolt_outlined,
        ),
        _infoPill(
          label: _outcomeLabel(item['desired_outcome']?.toString()),
          icon: Icons.track_changes_outlined,
        ),
        _infoPill(
          label: _noiseLabel(item['noise_category']?.toString()),
          icon: Icons.graphic_eq_outlined,
        ),
      ],
    );
  }

  Widget _buildRecommendationCard(Map<String, dynamic> item) {
    return _recordCard(
      icon: Icons.graphic_eq,
      title: item['title'] ?? 'Recomendación',
      createdAt: item['created_at'],
      pills: [
        _infoPill(
          label: _goalLabel(item['goal']?.toString()),
          icon: Icons.flag_outlined,
        ),
        _infoPill(
          label: '${item['target_bpm_range'] ?? '-'} BPM',
          icon: Icons.music_note_outlined,
        ),
        _infoPill(
          label: 'Energía ${_energyLabel(item['target_energy']?.toString())}',
          icon: Icons.bolt_outlined,
        ),
        _infoPill(
          label: 'Tono ${_valenceLabel(item['target_valence']?.toString())}',
          icon: Icons.light_mode_outlined,
        ),
      ],
    );
  }

  Widget _buildPlaylistCard(Map<String, dynamic> item) {
    return _recordCard(
      icon: Icons.queue_music,
      title: item['playlist_name'] ?? 'Playlist',
      createdAt: item['created_at'],
      trailing: IconButton(
        icon: const Icon(Icons.open_in_new),
        onPressed: () => _openUrl(item['playlist_url']?.toString()),
      ),
      pills: [
        _infoPill(
          label: _goalLabel(item['goal']?.toString()),
          icon: Icons.flag_outlined,
        ),
        _infoPill(
          label: '${item['tracks_added'] ?? 0} canciones',
          icon: Icons.queue_music_outlined,
        ),
        _infoPill(
          label: _outcomeLabel(item['desired_outcome']?.toString()),
          icon: Icons.track_changes_outlined,
        ),
        _infoPill(
          label:
              'Modo ${item['generation_mode']?.toString().replaceAll('_', ' ') ?? '-'}',
          icon: Icons.tune_outlined,
        ),
        _infoPill(
          label: item['ml_enabled'] == true
              ? 'Con aprendizaje'
              : 'Sin aprendizaje',
          icon: item['ml_enabled'] == true
              ? Icons.psychology_alt_outlined
              : Icons.rule_outlined,
        ),
      ],
    );
  }

  Widget _emptyStateCard({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFCF8),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFE7DBCD)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: const Color(0xFFE4EEE8),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(icon, color: const Color(0xFF204F46)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  subtitle,
                  style: const TextStyle(color: Color(0xFF5E645F), height: 1.4),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _loadMoreButton({
    required bool hasMore,
    required bool isLoading,
    required Future<void> Function() onTap,
    required String label,
  }) {
    if (!hasMore) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(top: 12, bottom: 4),
      child: Align(
        alignment: Alignment.centerLeft,
        child: FilledButton.tonal(
          onPressed: isLoading ? null : onTap,
          child: isLoading
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(label),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final filteredCheckins = checkins
        .where((item) => _matchesDateFilter(item['created_at']))
        .where(_matchesEmotion)
        .toList();
    final filteredRecommendations = recommendations
        .where((item) => _matchesDateFilter(item['created_at']))
        .where(_matchesGoal)
        .toList();
    final filteredPlaylists = generatedPlaylists
        .where((item) => _matchesDateFilter(item['created_at']))
        .where(_matchesGoal)
        .toList();
    final filteredFeedback = feedbackList
        .where((item) => _matchesDateFilter(item['created_at']))
        .toList();
    final totalItems =
        filteredCheckins.length +
        filteredRecommendations.length +
        filteredPlaylists.length +
        filteredFeedback.length;
    final summaryCheckins = totals?.checkins ?? filteredCheckins.length;
    final summaryPlaylists = totals?.playlists ?? filteredPlaylists.length;
    final summaryRecords = totals?.totalRecords ?? totalItems;

    return Scaffold(
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: loadHistory,
              child: DecoratedBox(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Color(0xFFF8F1E8),
                      Color(0xFFF1E7DA),
                      Color(0xFFE6ECE6),
                    ],
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
                          const Expanded(
                            child: Text(
                              'Historial',
                              style: TextStyle(
                                fontSize: 28,
                                fontWeight: FontWeight.w700,
                                color: Color(0xFF1F2421),
                              ),
                            ),
                          ),
                          const HomeShortcutButton(),
                        ],
                      ),
                      const SizedBox(height: 18),
                      StaggeredReveal(
                        order: 0,
                        child: Container(
                          clipBehavior: Clip.antiAlias,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(34),
                            gradient: const LinearGradient(
                              colors: [
                                Color(0xFF12312E),
                                Color(0xFF1F4A43),
                                Color(0xFF36665D),
                                Color(0xFFC9865B),
                              ],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x22000000),
                                blurRadius: 26,
                                offset: Offset(0, 16),
                              ),
                            ],
                          ),
                          child: Padding(
                            padding: const EdgeInsets.fromLTRB(24, 22, 24, 24),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'HISTORIAL PERSONAL',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 11,
                                    letterSpacing: 1.5,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 14),
                                const Text(
                                  '¿Te apetece un resumen histórico de tu actividad?',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 34,
                                    height: 0.96,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 18),
                      Row(
                        children: [
                          _summaryStat(
                            icon: Icons.favorite_outline,
                            label: 'Check-ins',
                            value: '$summaryCheckins',
                          ),
                          const SizedBox(width: 12),
                          _summaryStat(
                            icon: Icons.queue_music_rounded,
                            label: 'Playlists',
                            value: '$summaryPlaylists',
                          ),
                          const SizedBox(width: 12),
                          _summaryStat(
                            icon: Icons.rate_review_outlined,
                            label: 'Registros',
                            value: '$summaryRecords',
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      StaggeredReveal(
                        order: 1,
                        child: EditorialPanel(
                          accentColor: const Color(0xFFC8845A),
                          child: Padding(
                            padding: const EdgeInsets.all(18),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const EditorialSectionHeader(
                                  eyebrow: 'FILTROS',
                                  title: 'Actividad reciente',
                                ),
                                const SizedBox(height: 12),
                                const Text(
                                  'La actividad reciente se carga por bloques. Usa "Cargar más" en cada sección para recorrer el histórico completo sin disparar lecturas innecesarias.',
                                  style: TextStyle(
                                    color: Color(0xFF5E645F),
                                    height: 1.4,
                                  ),
                                ),
                                const SizedBox(height: 12),
                                const Text(
                                  'Vista',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF5E645F),
                                  ),
                                ),
                                const SizedBox(height: 10),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    _filterChip(
                                      label: 'Todo',
                                      selected: _viewFilter == 'todo',
                                      onTap: () =>
                                          setState(() => _viewFilter = 'todo'),
                                    ),
                                    _filterChip(
                                      label: 'Check-ins',
                                      selected: _viewFilter == 'checkins',
                                      onTap: () => setState(
                                        () => _viewFilter = 'checkins',
                                      ),
                                    ),
                                    _filterChip(
                                      label: 'Recomendaciones',
                                      selected:
                                          _viewFilter == 'recommendations',
                                      onTap: () => setState(
                                        () => _viewFilter = 'recommendations',
                                      ),
                                    ),
                                    _filterChip(
                                      label: 'Playlists',
                                      selected: _viewFilter == 'playlists',
                                      onTap: () => setState(
                                        () => _viewFilter = 'playlists',
                                      ),
                                    ),
                                    _filterChip(
                                      label: 'Feedback',
                                      selected: _viewFilter == 'feedback',
                                      onTap: () => setState(
                                        () => _viewFilter = 'feedback',
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 14),
                                const Text(
                                  'Emoción del check-in',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF5E645F),
                                  ),
                                ),
                                const SizedBox(height: 10),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    _filterChip(
                                      label: 'Todas',
                                      selected: _emotionFilter == 'todas',
                                      onTap: () => setState(
                                        () => _emotionFilter = 'todas',
                                      ),
                                    ),
                                    for (final emotion in const [
                                      'feliz',
                                      'neutral',
                                      'estresado',
                                      'triste',
                                      'cansado',
                                    ])
                                      _filterChip(
                                        label: emotion,
                                        selected: _emotionFilter == emotion,
                                        onTap: () => setState(
                                          () => _emotionFilter = emotion,
                                        ),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 14),
                                const Text(
                                  'Tipo de sesión',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF5E645F),
                                  ),
                                ),
                                const SizedBox(height: 10),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    _filterChip(
                                      label: 'Todos',
                                      selected: _goalFilter == 'todos',
                                      onTap: () =>
                                          setState(() => _goalFilter = 'todos'),
                                    ),
                                    for (final goal in const [
                                      'relajacion',
                                      'foco',
                                      'energia',
                                    ])
                                      _filterChip(
                                        label: _goalLabel(goal),
                                        selected: _goalFilter == goal,
                                        onTap: () =>
                                            setState(() => _goalFilter = goal),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 14),
                                const Text(
                                  'Periodo',
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFF5E645F),
                                  ),
                                ),
                                const SizedBox(height: 10),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: [
                                    _filterChip(
                                      label: 'Todo',
                                      selected: _daysFilter == 0,
                                      onTap: () =>
                                          setState(() => _daysFilter = 0),
                                    ),
                                    _filterChip(
                                      label: '7 días',
                                      selected: _daysFilter == 7,
                                      onTap: () =>
                                          setState(() => _daysFilter = 7),
                                    ),
                                    _filterChip(
                                      label: '30 días',
                                      selected: _daysFilter == 30,
                                      onTap: () =>
                                          setState(() => _daysFilter = 30),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      if (_viewFilter == 'todo' || _viewFilter == 'checkins')
                        _sectionTitle('Check-ins'),
                      if ((_viewFilter == 'todo' ||
                              _viewFilter == 'checkins') &&
                          filteredCheckins.isEmpty)
                        _emptyStateCard(
                          icon: Icons.favorite_outline,
                          title: 'No hay check-ins con estos filtros',
                          subtitle:
                              'Prueba a ampliar el periodo o quitar algún filtro para volver a ver tu recorrido.',
                        )
                      else if (_viewFilter == 'todo' ||
                          _viewFilter == 'checkins')
                        ...[
                          ...filteredCheckins.map(_buildCheckinCard),
                          _loadMoreButton(
                            hasMore: _hasMoreCheckins,
                            isLoading: _loadingMoreCheckins,
                            onTap: _loadMoreCheckins,
                            label: 'Cargar más check-ins',
                          ),
                        ],
                      if (_viewFilter == 'todo' ||
                          _viewFilter == 'recommendations')
                        _sectionTitle('Recomendaciones'),
                      if ((_viewFilter == 'todo' ||
                              _viewFilter == 'recommendations') &&
                          filteredRecommendations.isEmpty)
                        _emptyStateCard(
                          icon: Icons.auto_awesome_outlined,
                          title: 'No hay recomendaciones con estos filtros',
                          subtitle:
                              'Cuando haya coincidencias con el periodo o el tipo de sesión, aparecerán aquí.',
                        )
                      else if (_viewFilter == 'todo' ||
                          _viewFilter == 'recommendations')
                        ...[
                          ...filteredRecommendations.map(_buildRecommendationCard),
                          _loadMoreButton(
                            hasMore: _hasMoreRecommendations,
                            isLoading: _loadingMoreRecommendations,
                            onTap: _loadMoreRecommendations,
                            label: 'Cargar más recomendaciones',
                          ),
                        ],
                      if (_viewFilter == 'todo' || _viewFilter == 'playlists')
                        _sectionTitle('Playlists generadas'),
                      if ((_viewFilter == 'todo' ||
                              _viewFilter == 'playlists') &&
                          filteredPlaylists.isEmpty)
                        _emptyStateCard(
                          icon: Icons.queue_music_rounded,
                          title: 'No hay playlists con estos filtros',
                          subtitle:
                              'Aquí aparecerán las sesiones musicales que sí encajen con los filtros elegidos.',
                        )
                      else if (_viewFilter == 'todo' ||
                          _viewFilter == 'playlists')
                        ...[
                          ...filteredPlaylists.map(_buildPlaylistCard),
                          _loadMoreButton(
                            hasMore: _hasMorePlaylists,
                            isLoading: _loadingMorePlaylists,
                            onTap: _loadMorePlaylists,
                            label: 'Cargar más playlists',
                          ),
                        ],
                      if (_viewFilter == 'todo' || _viewFilter == 'feedback')
                        _sectionTitle('Feedback'),
                      if ((_viewFilter == 'todo' ||
                              _viewFilter == 'feedback') &&
                          filteredFeedback.isEmpty)
                        _emptyStateCard(
                          icon: Icons.rate_review_outlined,
                          title: 'No hay feedback con estos filtros',
                          subtitle:
                              'Tus valoraciones seguirán apareciendo aquí cuando entren dentro del periodo elegido.',
                        )
                      else if (_viewFilter == 'todo' ||
                          _viewFilter == 'feedback')
                        ...[
                          ...filteredFeedback.map(_buildFeedbackCard),
                          _loadMoreButton(
                            hasMore: _hasMoreFeedback,
                            isLoading: _loadingMoreFeedback,
                            onTap: _loadMoreFeedback,
                            label: 'Cargar más feedback',
                          ),
                        ],
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),
            ),
    );
  }
}
