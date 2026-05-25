import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:harmonyhub/features/preset_modes/domain/preset_mode.dart';

class SavedPresetModesFirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;

  static const String _collection = 'saved_preset_modes';

  Future<Set<String>> getMySavedModeIds() async {
    final user = _auth.currentUser;
    if (user == null) return <String>{};

    final snapshot = await _firestore
        .collection(_collection)
        .where('user_id', isEqualTo: user.uid)
        .get();

    return snapshot.docs
        .map((doc) => doc.data()['preset_mode_id']?.toString() ?? '')
        .where((id) => id.isNotEmpty)
        .toSet();
  }

  Future<void> saveMode(PresetMode mode) async {
    final user = _auth.currentUser;
    if (user == null) {
      throw Exception('Usuario no autenticado');
    }

    final docId = '${user.uid}_${mode.id}';

    await _firestore.collection(_collection).doc(docId).set({
      'user_id': user.uid,
      'preset_mode_id': mode.id,
      'title': mode.title,
      'subtitle': mode.subtitle,
      'description': mode.description,
      'goal': mode.goal,
      'suggested_mood': mode.suggestedMood,
      'suggested_outcome': mode.suggestedOutcome,
      'spotify_playlist_url': mode.spotifyPlaylistUrl,
      'created_at': FieldValue.serverTimestamp(),
      'updated_at': FieldValue.serverTimestamp(),
    }, SetOptions(merge: true));
  }

  Future<void> removeMode(PresetMode mode) async {
    final user = _auth.currentUser;
    if (user == null) {
      throw Exception('Usuario no autenticado');
    }

    final docId = '${user.uid}_${mode.id}';
    await _firestore.collection(_collection).doc(docId).delete();
  }
}
