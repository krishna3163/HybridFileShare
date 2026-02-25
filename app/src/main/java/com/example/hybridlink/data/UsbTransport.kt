package com.example.hybridlink.data

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.net.ServerSocket
import java.net.Socket
import java.net.InetSocketAddress
import java.util.concurrent.atomic.AtomicBoolean

class UsbTransport {
    private val isRunning = AtomicBoolean(false)
    private var serverSocket: ServerSocket? = null
    
    private val _status = MutableStateFlow(ConnectionStatus.DISCONNECTED)
    val status = _status.asStateFlow()

    suspend fun startServer(port: Int = 9000) = withContext(Dispatchers.IO) {
        isRunning.set(true)
        try {
            serverSocket = ServerSocket()
            serverSocket?.bind(InetSocketAddress("127.0.0.1", port))
            _status.value = ConnectionStatus.CONNECTED
            while (isRunning.get()) {
                val client = serverSocket?.accept() ?: break
                handleClient(client)
            }
        } catch (e: Exception) {
            _status.value = ConnectionStatus.ERROR
        } finally {
            _status.value = ConnectionStatus.DISCONNECTED
        }
    }

    private fun handleClient(socket: Socket) {
        CoroutineScope(Dispatchers.IO).launch {
            socket.use { s ->
                // Binary Chunk Protocol Implementation
            }
        }
    }

    fun stopServer() {
        isRunning.set(false)
        serverSocket?.close()
    }
}

enum class ConnectionStatus {
    CONNECTED,
    DISCONNECTED,
    ERROR
}
