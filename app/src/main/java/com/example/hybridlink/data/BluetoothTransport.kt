package com.example.hybridlink.data

import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothSocket
import android.content.Context
import android.util.Log
import java.util.UUID

class BluetoothTransport(private val context: Context) {
    private val TAG = "BluetoothTransport"
    private val APP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB") // SPP UUID
    
    private var bluetoothAdapter: BluetoothAdapter? = BluetoothAdapter.getDefaultAdapter()
    private var socket: BluetoothSocket? = null

    suspend fun startServer() {
        if (bluetoothAdapter == null) return
        
        try {
            val serverSocket = bluetoothAdapter?.listenUsingRfcommWithServiceRecord("HybridLink", APP_UUID)
            Log.d(TAG, "Bluetooth server started, waiting for connection...")
            
            socket = serverSocket?.accept()
            Log.d(TAG, "Bluetooth client connected")
            
            // Handle connection
            handleClient(socket!!)
        } catch (e: Exception) {
            Log.e(TAG, "Bluetooth server failed", e)
        }
    }

    private fun handleClient(socket: BluetoothSocket) {
        val inputStream = socket.inputStream
        val outputStream = socket.outputStream
        
        val buffer = ByteArray(1024)
        while (socket.isConnected) {
            try {
                val bytes = inputStream.read(buffer)
                if (bytes > 0) {
                    // Process received data
                }
            } catch (e: Exception) {
                break
            }
        }
    }

    fun stopServer() {
        socket?.close()
    }
}
