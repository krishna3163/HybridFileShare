package com.example.hybridlink.data

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.util.concurrent.ConcurrentHashMap

class MultiChannelScheduler(
    private val usbTransport: UsbTransport,
    private val wifiTransport: WifiTransport,
    private val chunkManager: ChunkManager
) {
    private val channelSpeeds = ConcurrentHashMap<String, Float>()
    private val activeJobs = ConcurrentHashMap<Int, Job>()

    fun startAdaptiveScheduling(scope: CoroutineScope) {
        scope.launch {
            flowOf(Pair(true, true)).collect { (usbReady, wifiReady) ->
                if (usbReady || wifiReady) {
                    processPendingChunks(scope, usbReady, wifiReady)
                }
            }
        }
    }

    private suspend fun processPendingChunks(scope: CoroutineScope, usbReady: Boolean, wifiReady: Boolean) {
        // Pending chunk mapping is managed dynamically via server sockets logic now
    }

    private fun selectBestChannel(usbReady: Boolean, wifiReady: Boolean): String {
        return when {
            usbReady && wifiReady -> {
                val usbSpeed = channelSpeeds["usb"] ?: 0f
                val wifiSpeed = channelSpeeds["wifi"] ?: 0f
                if (usbSpeed >= wifiSpeed) "usb" else "wifi"
            }
            usbReady -> "usb"
            wifiReady -> "wifi"
            else -> "none"
        }
    }

    private suspend fun transferChunk(chunkId: Int, channel: String) {
        try {
            // Actual transfer logic using selected transport
        } catch (e: Exception) {
            // Handle failure and retry
        } finally {
            activeJobs.remove(chunkId)
        }
    }
}
