package com.example.hybridlink.data

import kotlinx.coroutines.flow.Flow
import java.io.InputStream
import java.io.OutputStream

class WifiTransport {

    fun startServer(): Flow<ConnectionStatus> {
        // TODO: Implement TCP server for WiFi
        return kotlinx.coroutines.flow.emptyFlow()
    }

    fun connectToServer(ipAddress: String, port: Int): Flow<ConnectionStatus> {
        // TODO: Implement TCP client for WiFi
        return kotlinx.coroutines.flow.emptyFlow()
    }

    fun sendChunk(chunk: Chunk, inputStream: InputStream) {
        // TODO: Implement chunk sending over WiFi
    }

    fun receiveChunk(chunk: Chunk, outputStream: OutputStream) {
        // TODO: Implement chunk receiving over WiFi
    }

    fun disconnect() {
        // TODO: Implement disconnection logic
    }
}
