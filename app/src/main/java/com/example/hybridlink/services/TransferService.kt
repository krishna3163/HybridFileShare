package com.example.hybridlink.services

import android.app.*
import android.content.Intent
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.example.hybridlink.R
import kotlinx.coroutines.*
import java.io.DataOutputStream
import java.net.NetworkInterface
import java.net.ServerSocket
import java.net.Socket

/**
 * TransferService — Android foreground service that manages real file transfers.
 *
 * Responsibilities:
 *  - Opens control channel ServerSocket on port 5740
 *  - Advertises available NICs (WiFi IP, USB_ADB 127.0.0.1)
 *  - Accepts N transfer channel connections from PC client
 *  - Delegates to FileBlockSender/FileBlockReceiver for actual transfers
 */
class TransferService : Service() {

    companion object {
        private const val TAG = "TransferService"
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "hybridlink_transfer"
        const val CONTROL_PORT = 5740
    }

    inner class TransferBinder : Binder() {
        fun getService(): TransferService = this@TransferService
    }

    private val binder = TransferBinder()
    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var controlServer: ServerSocket? = null
    private var isRunning = false

    val transferSockets = mutableListOf<Socket>()
    val channelNames = mutableListOf<String>()

    var state: String = "idle"
        private set

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = buildNotification("HybridLink Transfer Engine is active")
        startForeground(NOTIFICATION_ID, notification)
        startControlServer()
        return START_STICKY
    }

    override fun onDestroy() {
        stop()
        serviceScope.cancel()
        super.onDestroy()
    }

    private fun startControlServer() {
        if (isRunning) return
        isRunning = true
        state = "waiting"

        serviceScope.launch {
            try {
                controlServer = ServerSocket(CONTROL_PORT)
                Log.i(TAG, "Control server listening on port $CONTROL_PORT")
                updateNotification("Waiting for PC connection on port $CONTROL_PORT")

                while (isRunning) {
                    val clientSocket = controlServer!!.accept()
                    Log.i(TAG, "Control connection from ${clientSocket.remoteSocketAddress}")
                    state = "connected"
                    updateNotification("Connected to ${clientSocket.inetAddress.hostAddress}")
                    sendNicList(clientSocket)
                    acceptTransferChannels()
                }
            } catch (e: Exception) {
                if (isRunning) {
                    Log.e(TAG, "Control server error: ${e.message}")
                }
            }
        }
    }

    fun getAvailableNics(): List<Pair<String, String>> {
        val nics = mutableListOf<Pair<String, String>>()
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (!iface.isUp || iface.isLoopback) continue
                if (iface.name.startsWith("rmnet") || iface.name.startsWith("tun")) continue
                for (addr in iface.inetAddresses) {
                    if (addr.isLoopbackAddress) continue
                    val ip = addr.hostAddress ?: continue
                    if (!ip.contains('.')) continue
                    nics.add(Pair(iface.name, ip))
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting NICs: ${e.message}")
        }
        nics.add(0, Pair("USB_ADB", "127.0.0.1"))
        return nics
    }

    private fun sendNicList(socket: Socket) {
        try {
            val dos = DataOutputStream(socket.getOutputStream())
            val nics = getAvailableNics()
            dos.writeInt(nics.size)
            for ((name, ip) in nics) {
                dos.writeUTF(name)
                dos.writeUTF(ip)
                val port = CONTROL_PORT + 1 + nics.indexOf(Pair(name, ip))
                dos.writeInt(port)
            }
            dos.flush()
            Log.i(TAG, "Sent ${nics.size} NICs to PC client")
        } catch (e: Exception) {
            Log.e(TAG, "Error sending NIC list: ${e.message}")
        }
    }

    private suspend fun acceptTransferChannels() {
        val nics = getAvailableNics()
        for ((idx, nic) in nics.withIndex()) {
            val port = CONTROL_PORT + 1 + idx
            serviceScope.launch {
                try {
                    val server = ServerSocket(port)
                    Log.i(TAG, "Transfer channel ${nic.first} listening on port $port")
                    val socket = server.accept()
                    synchronized(transferSockets) {
                        transferSockets.add(socket)
                        channelNames.add(nic.first)
                    }
                    Log.i(TAG, "Transfer channel ${nic.first} connected!")
                    server.close()
                } catch (e: Exception) {
                    Log.e(TAG, "Transfer channel ${nic.first} error: ${e.message}")
                }
            }
        }
    }

    fun stop() {
        isRunning = false
        state = "idle"
        try { controlServer?.close() } catch (_: Exception) { }
        transferSockets.forEach { try { it.close() } catch (_: Exception) { } }
        transferSockets.clear()
        channelNames.clear()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID, "HybridLink Transfer", NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(text: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("HybridLink Transfer Engine")
            .setContentText(text)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun updateNotification(text: String) {
        val notification = buildNotification(text)
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, notification)
    }
}
