package com.example.hybridlink.data

import kotlinx.coroutines.flow.Flow
import java.io.InputStream
import java.io.OutputStream

class UsbTransport {

    fun startServer(): Flow<ConnectionStatus> {
        // TODO: Implement TCP server for ADB forward
        return kotlinx.coroutines.flow.emptyFlow()
    }

    fun sendChunk(chunk: Chunk, inputStream: InputStream) {
        // TODO: Implement chunk sending over USB
    }

    fun receiveChunk(chunk: Chunk, outputStream: OutputStream) {
        // TODO: Implement chunk receiving over USB
    }

    fun stopServer() {
        // TODO: Implement server shutdown
    }
}

enum class ConnectionStatus {
    CONNECTED,
    DISCONNECTED,
    ERROR
}
