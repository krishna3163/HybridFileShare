package com.example.hybridlink.data

import android.content.Context
import java.io.File
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

data class QueuedTransfer(
    val id: String,
    val filePath: String,
    val destination: String,
    val isSending: Boolean,
    val timestamp: Long = System.currentTimeMillis()
)

class OfflineTransferQueue(private val context: Context) {
    private val queueFile = File(context.filesDir, "transfer_queue.json")

    fun addToQueue(transfer: QueuedTransfer) {
        val currentQueue = getQueue().toMutableList()
        currentQueue.add(transfer)
        saveQueue(currentQueue)
    }

    fun getQueue(): List<QueuedTransfer> {
        if (!queueFile.exists()) return emptyList()
        return try {
            Json.decodeFromString<List<QueuedTransfer>>(queueFile.readText())
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun saveQueue(queue: List<QueuedTransfer>) {
        val json = Json.encodeToString(queue)
        queueFile.writeText(json)
    }

    fun removeFirst(): QueuedTransfer? {
        val queue = getQueue().toMutableList()
        if (queue.isEmpty()) return null
        val first = queue.removeAt(0)
        saveQueue(queue)
        return first
    }
}
