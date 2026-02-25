package com.example.hybridlink.util

import android.graphics.Bitmap
import android.util.Base64
import com.example.hybridlink.model.DeviceMetadata
import com.google.zxing.BarcodeFormat
import com.google.zxing.MultiFormatWriter
import com.google.zxing.common.BitMatrix
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.security.KeyPairGenerator
import java.security.SecureRandom

class PairingManager {
    
    private var activePin: String? = null
    private var pinExpiry: Long = 0

    fun generatePairingQR(deviceMetadata: DeviceMetadata, publicKey: ByteArray): Bitmap? {
        val payload = mapOf(
            "id" to deviceMetadata.id,
            "name" to deviceMetadata.name,
            "key" to Base64.encodeToString(publicKey, Base64.DEFAULT),
            "ts" to System.currentTimeMillis()
        )
        val data = Json.encodeToString(payload)
        
        return try {
            val bitMatrix: BitMatrix = MultiFormatWriter().encode(data, BarcodeFormat.QR_CODE, 512, 512)
            val width = bitMatrix.width
            val height = bitMatrix.height
            val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.RGB_565)
            for (x in 0 until width) {
                for (y in 0 until height) {
                    bitmap.setPixel(x, y, if (bitMatrix.get(x, y)) android.graphics.Color.BLACK else android.graphics.Color.WHITE)
                }
            }
            bitmap
        } catch (e: Exception) {
            null
        }
    }

    fun generatePIN(): String {
        val pin = (100000..999999).random().toString()
        activePin = pin
        pinExpiry = System.currentTimeMillis() + 300000 // 5 mins
        return pin
    }

    fun verifyPIN(enteredPin: String): Boolean {
        if (activePin == null || System.currentTimeMillis() > pinExpiry) return false
        val isValid = enteredPin == activePin
        if (isValid) activePin = null
        return isValid
    }
}
