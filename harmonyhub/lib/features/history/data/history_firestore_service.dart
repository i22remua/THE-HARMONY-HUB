import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:harmonyhub/core/security/emotion_encryption_service.dart';

class HistoryFirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final EmotionEncryptionService _emotionEncryptionService =
      EmotionEncryptionService();

  Future<String?> _currentUserId() async {
    final user = _auth.currentUser;
    return user?.uid;
  }

  Future<int> _countForCollection(String collectionName) async {
    final userId = await _currentUserId();
    if (userId == null) return 0;

    final aggregate = await _firestore
        .collection(collectionName)
        .where('user_id', isEqualTo: userId)
        .count()
        .get();

    return aggregate.count ?? 0;
  }

  Query<Map<String, dynamic>> _baseHistoryQuery(
    String collectionName,
    String userId, {
    required int limit,
    dynamic startAfterCreatedAt,
  }) {
    var query = _firestore
        .collection(collectionName)
        .where('user_id', isEqualTo: userId)
        .orderBy('created_at', descending: true)
        .limit(limit);

    if (startAfterCreatedAt != null) {
      query = query.startAfter([startAfterCreatedAt]);
    }

    return query;
  }

  // Reconstruye el historial de check-ins uniendo el documento público con su
  // bloque privado cifrado cuando existe. Así la UI puede mostrar contexto útil
  // sin exponer siempre los datos emocionales en la colección pública.
  Future<HistoryPage> getMyCheckinsPage({
    int limit = 15,
    dynamic startAfterCreatedAt,
  }) async {
    final userId = await _currentUserId();
    if (userId == null) return const HistoryPage.empty();

    final snapshot = await _baseHistoryQuery(
      'checkins',
      userId,
      limit: limit,
      startAfterCreatedAt: startAfterCreatedAt,
    ).get();

    final items = await Future.wait(
      snapshot.docs.map((doc) async {
        final data = Map<String, dynamic>.from(doc.data());
        data['id'] = doc.id;

        final hasEncryptedEmotionData =
            data['has_encrypted_emotion_data'] == true;
        final privateRefId = data['private_ref_id']?.toString();

        if (!hasEncryptedEmotionData ||
            privateRefId == null ||
            privateRefId.isEmpty) {
          return data;
        }

        try {
          final privateSnapshot = await _firestore
              .collection('checkins_private')
              .doc(privateRefId)
              .get();

          if (!privateSnapshot.exists) {
            return data;
          }

          final privateData = privateSnapshot.data();
          if (privateData == null) {
            return data;
          }

          final decrypted = await _emotionEncryptionService.decryptPayload(
            uid: userId,
            encryptedPayload: privateData,
          );

          data.addAll({
            'mood': decrypted['mood'],
            'goal': decrypted['goal'],
            'stress_level': decrypted['stress_level'],
            'energy_level': decrypted['energy_level'],
            'desired_outcome': decrypted['desired_outcome'],
          });
        } catch (_) {
          // Si falla el descifrado, el historial sigue mostrando la parte pública.
        }

        return data;
      }),
    );

    return HistoryPage(
      items: items,
      cursor: snapshot.docs.isNotEmpty
          ? snapshot.docs.last.data()['created_at']
          : null,
      hasMore: snapshot.docs.length == limit,
    );
  }

  // Las recomendaciones ya se guardan en una forma suficientemente visible, por
  // lo que aquí basta con recuperar el documento y añadir su id para enlazarlo
  // después con detalle, playlist o feedback asociado.
  Future<HistoryPage> getMyRecommendationsPage({
    int limit = 15,
    dynamic startAfterCreatedAt,
  }) async {
    final userId = await _currentUserId();
    if (userId == null) return const HistoryPage.empty();

    final snapshot = await _baseHistoryQuery(
      'recommendations',
      userId,
      limit: limit,
      startAfterCreatedAt: startAfterCreatedAt,
    ).get();

    final items = snapshot.docs.map((doc) {
      final data = doc.data();
      data['id'] = doc.id;
      return data;
    }).toList();

    return HistoryPage(
      items: items,
      cursor: snapshot.docs.isNotEmpty
          ? snapshot.docs.last.data()['created_at']
          : null,
      hasMore: snapshot.docs.length == limit,
    );
  }

  // El feedback repite el mismo patrón de privacidad que los check-ins: la
  // colección pública conserva la traza mínima y el bloque privado contiene la
  // valoración completa, que se descifra solo para el propietario.
  Future<HistoryPage> getMyFeedbackPage({
    int limit = 15,
    dynamic startAfterCreatedAt,
  }) async {
    final userId = await _currentUserId();
    if (userId == null) return const HistoryPage.empty();

    final snapshot = await _baseHistoryQuery(
      'feedback',
      userId,
      limit: limit,
      startAfterCreatedAt: startAfterCreatedAt,
    ).get();

    final items = await Future.wait(
      snapshot.docs.map((doc) async {
        final data = Map<String, dynamic>.from(doc.data());
        data['id'] = doc.id;

        final hasEncryptedFeedbackData =
            data['has_encrypted_feedback_data'] == true ||
            data['has_encrypted_emotion_data'] == true;
        final privateRefId = data['private_ref_id']?.toString();

        if (!hasEncryptedFeedbackData ||
            privateRefId == null ||
            privateRefId.isEmpty) {
          return data;
        }

        try {
          final privateSnapshot = await _firestore
              .collection('feedback_private')
              .doc(privateRefId)
              .get();

          if (!privateSnapshot.exists) {
            return data;
          }

          final privateData = privateSnapshot.data();
          if (privateData == null) {
            return data;
          }

          final decrypted = await _emotionEncryptionService.decryptPayload(
            uid: userId,
            encryptedPayload: privateData,
          );

          data.addAll({
            'helpful': decrypted['helpful'],
            'effect': decrypted['effect'],
            'post_session_state': decrypted['post_session_state'],
            'comment': decrypted['comment'],
          });
        } catch (_) {
          // Si falla el descifrado, el histórico sigue mostrando la parte pública.
        }

        return data;
      }),
    );

    return HistoryPage(
      items: items,
      cursor: snapshot.docs.isNotEmpty
          ? snapshot.docs.last.data()['created_at']
          : null,
      hasMore: snapshot.docs.length == limit,
    );
  }

  // Las playlists generadas son el cierre visible del flujo principal. Se
  // recuperan tal cual para que historial y detalle de sesión puedan reconstruir
  // qué recomendación acabó materializada en Spotify.
  Future<HistoryPage> getMyGeneratedPlaylistsPage({
    int limit = 15,
    dynamic startAfterCreatedAt,
  }) async {
    final userId = await _currentUserId();
    if (userId == null) return const HistoryPage.empty();

    final snapshot = await _baseHistoryQuery(
      'generated_playlists',
      userId,
      limit: limit,
      startAfterCreatedAt: startAfterCreatedAt,
    ).get();

    final items = snapshot.docs.map((doc) {
      final data = doc.data();
      data['id'] = doc.id;
      return data;
    }).toList();

    return HistoryPage(
      items: items,
      cursor: snapshot.docs.isNotEmpty
          ? snapshot.docs.last.data()['created_at']
          : null,
      hasMore: snapshot.docs.length == limit,
    );
  }

  Future<HistoryTotals> getMyHistoryTotals() async {
    final results = await Future.wait([
      _countForCollection('checkins'),
      _countForCollection('recommendations'),
      _countForCollection('feedback'),
      _countForCollection('generated_playlists'),
    ]);

    return HistoryTotals(
      checkins: results[0],
      recommendations: results[1],
      feedback: results[2],
      playlists: results[3],
    );
  }
}

class HistoryPage {
  final List<Map<String, dynamic>> items;
  final dynamic cursor;
  final bool hasMore;

  const HistoryPage({
    required this.items,
    required this.cursor,
    required this.hasMore,
  });

  const HistoryPage.empty() : this(items: const [], cursor: null, hasMore: false);
}

class HistoryTotals {
  final int checkins;
  final int recommendations;
  final int feedback;
  final int playlists;

  const HistoryTotals({
    required this.checkins,
    required this.recommendations,
    required this.feedback,
    required this.playlists,
  });

  int get totalRecords => checkins + recommendations + feedback + playlists;
}
