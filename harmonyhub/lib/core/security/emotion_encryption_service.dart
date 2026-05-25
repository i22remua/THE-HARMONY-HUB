import 'dart:convert';
import 'dart:math';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class EmotionEncryptionService {
  EmotionEncryptionService();

  static const FlutterSecureStorage _secureStorage = FlutterSecureStorage();
  static final AesGcm _algorithm = AesGcm.with256bits();

  String _storageKeyForUser(String uid) => 'emotion_key_v1_$uid';

  Future<SecretKey> _getOrCreateKey(String uid) async {
    final existing = await _secureStorage.read(key: _storageKeyForUser(uid));

    if (existing != null && existing.isNotEmpty) {
      final bytes = base64Decode(existing);
      return SecretKey(bytes);
    }

    final random = Random.secure();
    final keyBytes = List<int>.generate(32, (_) => random.nextInt(256));

    await _secureStorage.write(
      key: _storageKeyForUser(uid),
      value: base64Encode(keyBytes),
    );

    return SecretKey(keyBytes);
  }

  Future<Map<String, dynamic>> encryptPayload({
    required String uid,
    required Map<String, dynamic> payload,
  }) async {
    final secretKey = await _getOrCreateKey(uid);
    final jsonString = jsonEncode(payload);
    final clearBytes = utf8.encode(jsonString);

    final nonce = _algorithm.newNonce();
    final secretBox = await _algorithm.encrypt(
      clearBytes,
      secretKey: secretKey,
      nonce: nonce,
    );

    return {
      'algorithm': 'AES_GCM_256',
      'schema_version': 1,
      'ciphertext': base64Encode(secretBox.cipherText),
      'nonce': base64Encode(secretBox.nonce),
      'mac': base64Encode(secretBox.mac.bytes),
    };
  }

  Future<Map<String, dynamic>> decryptPayload({
    required String uid,
    required Map<String, dynamic> encryptedPayload,
  }) async {
    final secretKey = await _getOrCreateKey(uid);

    final cipherText = base64Decode(
      encryptedPayload['ciphertext']?.toString() ?? '',
    );
    final nonce = base64Decode(
      encryptedPayload['nonce']?.toString() ?? '',
    );
    final macBytes = base64Decode(
      encryptedPayload['mac']?.toString() ?? '',
    );

    final secretBox = SecretBox(
      cipherText,
      nonce: nonce,
      mac: Mac(macBytes),
    );

    final clearBytes = await _algorithm.decrypt(
      secretBox,
      secretKey: secretKey,
    );

    final jsonString = utf8.decode(clearBytes);
    final decoded = jsonDecode(jsonString);

    return Map<String, dynamic>.from(decoded as Map);
  }
}