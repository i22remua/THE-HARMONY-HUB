import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:harmonyhub/core/security/emotion_encryption_service.dart';
import 'package:harmonyhub/features/checkin/data/environment_audio_profile.dart';

class CheckinFirestoreService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final EmotionEncryptionService _emotionEncryptionService =
      EmotionEncryptionService();

  Future<void> saveCheckin({
    required String mood,
    required String goal,
    required int stressLevel,
    required int energyLevel,
    required EnvironmentAudioProfile audioProfile,
    String? desiredOutcome,
  }) async {
    final user = _auth.currentUser;
    if (user == null) {
      throw Exception('Usuario no autenticado');
    }

    final docRef = _firestore.collection('checkins').doc();
    final privateRef = _firestore.collection('checkins_private').doc(docRef.id);

    final encryptedEmotionBlock =
        await _emotionEncryptionService.encryptPayload(
      uid: user.uid,
      payload: {
        'mood': mood,
        'goal': goal,
        'stress_level': stressLevel,
        'energy_level': energyLevel,
        'desired_outcome': desiredOutcome,
      },
    );

    final batch = _firestore.batch();

    batch.set(docRef, {
      'user_id': user.uid,
      ...audioProfile.toPublicFirestoreMap(),
      'has_encrypted_emotion_data': true,
      'private_ref_id': privateRef.id,
      'created_at': FieldValue.serverTimestamp(),
    });

    batch.set(privateRef, {
      'user_id': user.uid,
      'checkin_id': docRef.id,
      ...encryptedEmotionBlock,
      'created_at': FieldValue.serverTimestamp(),
    });

    await batch.commit();
  }
}