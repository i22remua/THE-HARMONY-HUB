import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class GeneratedPlaylistFirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  Future<void> saveGeneratedPlaylist({
    String? recommendationId,
    required String playlistId,
    required String playlistName,
    required String playlistUrl,
    required int tracksAdded,
    required String recommendedMode,
    String? generationMode,
    required String goal,
    required String noiseCategory,
    String? spotifyUserId,
    bool mlEnabled = false,
    String? desiredOutcome,
    int feedbackCount = 0,
    double sessionTasteWeight = 0.0,
    double stableTasteWeight = 0.0,
    String tasteProfileMode = 'session_weighted',
    bool environmentMeasured = false,
    bool useEnvironment = false,
    String? environmentContext,
    double? environmentConfidence,
    double? environmentStabilityScore,
    double? environmentSampleDensityHz,
    String? environmentUsageStatus,
    String? environmentUsageRationale,
    List<Map<String, dynamic>> selectedTracks = const [],
  }) async {
    // Persiste la playlist generada con el contexto de sesión y los tracks
    // elegidos para poder auditar después cómo decidió el sistema.
    final user = _auth.currentUser;
    if (user == null) {
      throw Exception('Usuario no autenticado');
    }

    await _firestore.collection('generated_playlists').add({
      'user_id': user.uid,
      'spotify_user_id': spotifyUserId,
      'recommendation_id': recommendationId,
      'playlist_id': playlistId,
      'playlist_name': playlistName,
      'playlist_url': playlistUrl,
      'tracks_added': tracksAdded,
      'recommended_mode': recommendedMode,
      'generation_mode': generationMode,
      'goal': goal,
      'noise_category': noiseCategory,
      'ml_enabled': mlEnabled,
      'desired_outcome': desiredOutcome,
      'feedback_count': feedbackCount,
      'session_taste_weight': sessionTasteWeight,
      'stable_taste_weight': stableTasteWeight,
      'taste_profile_mode': tasteProfileMode,
      'environment_measured': environmentMeasured,
      'use_environment': useEnvironment,
      'environment_context': environmentContext,
      'environment_confidence': environmentConfidence,
      'environment_stability_score': environmentStabilityScore,
      'environment_sample_density_hz': environmentSampleDensityHz,
      'environment_usage_status': environmentUsageStatus,
      'environment_usage_rationale': environmentUsageRationale,
      'selected_tracks': selectedTracks,
      'created_at': FieldValue.serverTimestamp(),
    });
  }
}
