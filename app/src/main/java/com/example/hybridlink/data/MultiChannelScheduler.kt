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
            combine(usbTransport.status, wifiTransport.status) { usb, wifi ->
                usb == ConnectionStatus.CONNECTED to (wifi == ConnectionStatus.CONNECTED)
            }.collect { (usbReady, wifiReady) ->
                if (usbReady || wifiReady) {
                    processPendingChunks(scope, usbReady, wifiReady)
                }
            }
        }
    }

    private suspend fun processPendingChunks(scope: CoroutineScope, usbReady: Boolean, wifiReady: Boolean) {
        chunkManager.getPendingChunks().forEach { chunk ->
            if (!activeJobs.containsKey(chunk.id)) {
                val bestChannel = selectBestChannel(usbReady, wifiReady)
                activeJobs[chunk.id] = scope.launch(Dispatchers.IO) {
                    transferChunk(chunk, bestChannel)
                }
            }
        }
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

    private suspend fun transferChunk(chunk: Chunk, channel: String) {
        try {
            // Actual transfer logic using selected transport
            // Update channelSpeeds based on results
        } catch (e: Exception) {
            // Handle failure and retry
        } finally {
            activeJobs.remove(chunk.id)
        }
    }
}
