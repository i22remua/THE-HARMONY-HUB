import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:harmonyhub/core/security/emotion_encryption_service.dart';

class FeedbackFirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final EmotionEncryptionService _emotionEncryptionService =
      EmotionEncryptionService();

  Future<void> saveFeedback({
    required String recommendationId,
    required String recommendationTitle,
    required bool helpful,
    required String effect,
    required String postSessionState,
    String? comment,
    bool useForTasteProfile = true,
    String preferenceScope = 'both',
  }) async {
    // Guarda una copia mínima del feedback en Firestore para histórico y
    // trazabilidad del lado cliente.
    final user = _auth.currentUser;
    if (user == null) {
      throw Exception('Usuario no autenticado');
    }

    final docRef = _firestore.collection('feedback').doc();
    final privateRef = _firestore.collection('feedback_private').doc(docRef.id);

    final encryptedFeedbackBlock =
        await _emotionEncryptionService.encryptPayload(
      uid: user.uid,
      payload: {
        'helpful': helpful,
        'effect': effect,
        'post_session_state': postSessionState,
        'comment': (comment == null || comment.trim().isEmpty)
            ? null
            : comment.trim(),
      },
    );

    final batch = _firestore.batch();

    batch.set(docRef, {
      'user_id': user.uid,
      'recommendation_id': recommendationId,
      'recommendation_title': recommendationTitle,
      'helpful': helpful,
      'effect': effect,
      'post_session_state': postSessionState,
      'comment': (comment == null || comment.trim().isEmpty)
          ? null
          : comment.trim(),
      'use_for_taste_profile': useForTasteProfile,
      'preference_scope': preferenceScope,
      'has_encrypted_feedback_data': true,
      'private_ref_id': privateRef.id,
      'created_at': FieldValue.serverTimestamp(),
    });

    batch.set(privateRef, {
      'user_id': user.uid,
      'feedback_id': docRef.id,
      ...encryptedFeedbackBlock,
      'created_at': FieldValue.serverTimestamp(),
    });

    await batch.commit();
  }
}
