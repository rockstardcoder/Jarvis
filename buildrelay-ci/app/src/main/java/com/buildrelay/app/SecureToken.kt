package com.buildrelay.app

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureToken(private val context: Context) {
  private val prefs = context.getSharedPreferences("buildrelay_secure", Context.MODE_PRIVATE)
  private val alias = "buildrelay_github"

  private fun key(): SecretKey {
    val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
    (ks.getKey(alias, null) as? SecretKey)?.let { return it }
    val kg = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
    kg.init(
      KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
        .build()
    )
    return kg.generateKey()
  }

  fun save(value: String) {
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.ENCRYPT_MODE, key())
    val encrypted = cipher.doFinal(value.toByteArray())
    prefs.edit()
      .putString("iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
      .putString("data", Base64.encodeToString(encrypted, Base64.NO_WRAP))
      .apply()
  }

  fun read(): String? = runCatching {
    val ivText = prefs.getString("iv", null) ?: return null
    val dataText = prefs.getString("data", null) ?: return null
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(ivText, Base64.NO_WRAP)))
    String(cipher.doFinal(Base64.decode(dataText, Base64.NO_WRAP)))
  }.getOrNull()

  fun clear() { prefs.edit().clear().apply() }
}
