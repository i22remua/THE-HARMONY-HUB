import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class UserLearningFirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  Future<Map<String, dynamic>?> getMyLearningProfile() async {
    final user = _auth.currentUser;
    if (user == null) return null;

    final snapshot = await _firestore
        .collection('generated_playlists')
        .where('user_id', isEqualTo: user.uid)
        .orderBy('created_at', descending: true)
        .limit(1)
        .get(const GetOptions(source: Source.serverAndCache));

    if (snapshot.docs.isEmpty) {
      return null;
    }

    final latestGeneratedPlaylist = snapshot.docs.first.data();
    final spotifyUserId = latestGeneratedPlaylist['spotify_user_id']
        ?.toString();

    if (spotifyUserId == null || spotifyUserId.isEmpty) {
      return {
        'spotify_user_id': null,
        'preferred_genres': <String>[],
        'avoided_genres': <String>[],
        'genre_scores': <String, dynamic>{},
        'feedback_count': 0,
        'positive_feedback_count': 0,
        'negative_feedback_count': 0,
      };
    }

    final prefDoc = await _firestore
        .collection('user_generation_preferences')
        .doc(spotifyUserId)
        .get(const GetOptions(source: Source.serverAndCache));

    if (!prefDoc.exists) {
      return {
        'spotify_user_id': spotifyUserId,
        'preferred_genres': <String>[],
        'avoided_genres': <String>[],
        'genre_scores': <String, dynamic>{},
        'feedback_count': 0,
        'positive_feedback_count': 0,
        'negative_feedback_count': 0,
      };
    }

    final data = prefDoc.data() ?? {};
    final preferredGenresMap = Map<String, dynamic>.from(
      data['preferred_genres'] ?? {},
    );
    final avoidedGenresMap = Map<String, dynamic>.from(
      data['avoided_genres'] ?? {},
    );
    final genreScoresMap = Map<String, dynamic>.from(
      data['genre_scores'] ?? {},
    );

    List<String> positiveNetGenres({
      required Map<String, dynamic> preferred,
      required Map<String, dynamic> genreScores,
    }) {
      final entries =
          preferred.entries.where((entry) {
            final netScore = (genreScores[entry.key] as num?)?.toDouble();
            return netScore == null || netScore > 0;
          }).toList()..sort((a, b) {
            final aNet =
                (genreScores[a.key] as num?)?.toDouble() ??
                ((a.value as num?)?.toDouble() ?? 0);
            final bNet =
                (genreScores[b.key] as num?)?.toDouble() ??
                ((b.value as num?)?.toDouble() ?? 0);
            return bNet.compareTo(aNet);
          });

      return entries.map((e) => e.key).toList();
    }

    List<String> negativeNetGenres({
      required Map<String, dynamic> avoided,
      required Map<String, dynamic> genreScores,
      required Set<String> alreadyPreferred,
    }) {
      final entries =
          avoided.entries.where((entry) {
            final netScore = (genreScores[entry.key] as num?)?.toDouble();
            if (netScore != null) {
              return netScore < 0;
            }
            return !alreadyPreferred.contains(entry.key);
          }).toList()..sort((a, b) {
            final aNet = (genreScores[a.key] as num?)?.toDouble();
            final bNet = (genreScores[b.key] as num?)?.toDouble();

            if (aNet != null && bNet != null) {
              return aNet.compareTo(bNet);
            }

            final aValue = (a.value as num?)?.toDouble() ?? 0;
            final bValue = (b.value as num?)?.toDouble() ?? 0;
            return bValue.compareTo(aValue);
          });

      return entries.map((e) => e.key).toList();
    }

    final resolvedPreferredGenres = positiveNetGenres(
      preferred: preferredGenresMap,
      genreScores: genreScoresMap,
    );
    final resolvedAvoidedGenres = negativeNetGenres(
      avoided: avoidedGenresMap,
      genreScores: genreScoresMap,
      alreadyPreferred: resolvedPreferredGenres.toSet(),
    );

    return {
      'spotify_user_id': spotifyUserId,
      'preferred_genres': resolvedPreferredGenres,
      'avoided_genres': resolvedAvoidedGenres,
      'genre_scores': genreScoresMap,
      'preferred_valence': data['preferred_valence'],
      'preferred_energy': data['preferred_energy'],
      'preferred_danceability': data['preferred_danceability'],
      'session_preferred_valence': data['session_preferred_valence'],
      'session_preferred_energy': data['session_preferred_energy'],
      'session_preferred_danceability': data['session_preferred_danceability'],
      'stable_preferred_valence': data['stable_preferred_valence'],
      'stable_preferred_energy': data['stable_preferred_energy'],
      'stable_preferred_danceability': data['stable_preferred_danceability'],
      'feedback_count': data['feedback_count'] ?? 0,
      'positive_feedback_count': data['positive_feedback_count'] ?? 0,
      'negative_feedback_count': data['negative_feedback_count'] ?? 0,
      'session_feedback_count': data['session_feedback_count'] ?? 0,
      'session_positive_feedback_count':
          data['session_positive_feedback_count'] ?? 0,
      'session_negative_feedback_count':
          data['session_negative_feedback_count'] ?? 0,
      'stable_feedback_count': data['stable_feedback_count'] ?? 0,
      'stable_positive_feedback_count':
          data['stable_positive_feedback_count'] ?? 0,
      'stable_negative_feedback_count':
          data['stable_negative_feedback_count'] ?? 0,
    };
  }
}
