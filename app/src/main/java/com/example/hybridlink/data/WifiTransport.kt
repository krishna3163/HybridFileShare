package com.example.hybridlink.data

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.net.ServerSocket
import java.net.Socket
import java.net.InetSocketAddress
import java.util.concurrent.atomic.AtomicBoolean
import java.io.DataInputStream

class WifiTransport(private val chunkManager: ChunkManager? = null) {
    private val isRunning = AtomicBoolean(false)
    private var serverSocket: ServerSocket? = null
    
    private val _status = MutableStateFlow(ConnectionStatus.DISCONNECTED)
    val status = _status.asStateFlow()

    suspend fun startServer(port: Int = 9001) = withContext(Dispatchers.IO) {
        isRunning.set(true)
        try {
            serverSocket = ServerSocket()
            serverSocket?.bind(InetSocketAddress("0.0.0.0", port))
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
                val input = DataInputStream(s.getInputStream())
                while (s.isConnected && !s.isClosed && isRunning.get()) {
                    try {
                        val chunkId = input.readInt()
                        val size = input.readInt()
                        if (size <= 0 || size > 100 * 1024 * 1024) break // sanity check
                        
                        val buffer = ByteArray(size)
                        input.readFully(buffer)
                        
                        chunkManager?.writeChunk(chunkId, buffer)
                    } catch (e: Exception) {
                        break
                    }
                }
            }
        }
    }

    fun stopServer() {
        isRunning.set(false)
        try { serverSocket?.close() } catch (e: Exception) {}
    }
}
