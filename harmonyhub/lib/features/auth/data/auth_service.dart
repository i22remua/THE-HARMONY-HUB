import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  String _normalizeEmail(String email) => email.trim().toLowerCase();

  Future<void> register({
    required String email,
    required String password,
  }) async {
    final normalizedEmail = _normalizeEmail(email);
    final credential = await _auth.createUserWithEmailAndPassword(
      email: normalizedEmail,
      password: password,
    );

    final user = credential.user;
    if (user != null) {
      await _firestore.collection('users').doc(user.uid).set({
        'uid': user.uid,
        'email': user.email,
        'email_normalized': normalizedEmail,
        'created_at': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));
    }
  }

  Future<void> login({required String email, required String password}) async {
    await _auth.signInWithEmailAndPassword(
      email: _normalizeEmail(email),
      password: password,
    );
  }

  Future<void> logout() async {
    await _auth.signOut();
    SpotifySession.instance.clear();
  }

  Future<void> sendPasswordReset({required String email}) async {
    final trimmedEmail = email.trim();
    final normalizedEmail = _normalizeEmail(email);
    String resetEmail = trimmedEmail;

    final normalizedMatch = await _firestore
        .collection('users')
        .where('email_normalized', isEqualTo: normalizedEmail)
        .limit(1)
        .get();

    if (normalizedMatch.docs.isNotEmpty) {
      resetEmail =
          (normalizedMatch.docs.first.data()['email'] as String?)
                  ?.trim()
                  .isNotEmpty ==
              true
          ? (normalizedMatch.docs.first.data()['email'] as String).trim()
          : normalizedEmail;
    } else {
      final directMatch = await _firestore
          .collection('users')
          .where('email', isEqualTo: trimmedEmail)
          .limit(1)
          .get();

      if (directMatch.docs.isNotEmpty) {
        resetEmail =
            (directMatch.docs.first.data()['email'] as String?)
                    ?.trim()
                    .isNotEmpty ==
                true
            ? (directMatch.docs.first.data()['email'] as String).trim()
            : trimmedEmail;
      }
    }

    await _auth.sendPasswordResetEmail(email: resetEmail);
  }
}
