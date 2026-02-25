package com.example.hybridlink.data

import android.content.Context
import com.example.hybridlink.model.FileMetadata
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

class TransferEngine(
    private val context: Context,
    private val usbTransport: UsbTransport,
    private val wifiTransport: WifiTransport,
    private val chunkManager: ChunkManager,
    private val scheduler: MultiChannelScheduler
) {
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var transferJob: Job? = null

    private val _progress = MutableStateFlow(0f)
    val progress = _progress.asStateFlow()

    private val _status = MutableStateFlow("Idle")
    val status = _status.asStateFlow()

    fun startTransfer(file: File, isSending: Boolean) {
        transferJob?.cancel()
        transferJob = scope.launch {
            _status.value = if (isSending) "Sending..." else "Receiving..."
            
            // Register channels
            launch { usbTransport.startServer() }
            launch { wifiTransport.startServer() }
            
            scheduler.startAdaptiveScheduling(this)
            
            // Monitor progress and update StateFlow
            // (In a real app, this would be highly detailed)
        }
    }

    fun pauseTransfer() {
        // Implementation for pausing
        _status.value = "Paused"
    }

    fun cancelTransfer() {
        transferJob?.cancel()
        usbTransport.stopServer()
        wifiTransport.stopServer()
        _status.value = "Idle"
        _progress.value = 0f
    }
}
