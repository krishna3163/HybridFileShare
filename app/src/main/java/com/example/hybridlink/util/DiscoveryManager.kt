package com.example.hybridlink.util

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.util.Log
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class DiscoveryManager(private val context: Context) {
    private val TAG = "DiscoveryManager"
    private val SERVICE_TYPE = "_hybridlink._tcp."
    private val DISCOVERY_PORT = 8888
    
    private var nsdManager: NsdManager? = null
    private var registrationListener: NsdManager.RegistrationListener? = null

    interface DiscoveryListener {
        fun onDeviceFound(name: String, address: String, port: Int)
    }

    suspend fun startBroadcasting(deviceName: String, port: Int) = withContext(Dispatchers.IO) {
        // mDNS Registration
        val serviceInfo = NsdServiceInfo().apply {
            serviceName = deviceName
            serviceType = SERVICE_TYPE
            setPort(port)
        }

        nsdManager = (context.getSystemService(Context.NSD_SERVICE) as NsdManager).apply {
            registrationListener = object : NsdManager.RegistrationListener {
                override fun onServiceRegistered(NsdServiceInfo: NsdServiceInfo) {
                    Log.d(TAG, "Service registered: ${NsdServiceInfo.serviceName}")
                }
                override fun onRegistrationFailed(arg0: NsdServiceInfo, arg1: Int) {}
                override fun onServiceUnregistered(arg0: NsdServiceInfo) {}
                override fun onUnregistrationFailed(arg0: NsdServiceInfo, arg1: Int) {}
            }
            registerService(serviceInfo, NsdManager.PROTOCOL_DNS_SD, registrationListener)
        }

        // UDP Broadcast for faster discovery
        try {
            val socket = DatagramSocket()
            socket.broadcast = true
            val message = "HYBRIDLINK_DISCOVERY:$deviceName:$port".toByteArray()
            val packet = DatagramPacket(message, message.size, InetAddress.getByName("255.255.255.255"), DISCOVERY_PORT)
            
            while (true) {
                socket.send(packet)
                kotlinx.coroutines.delay(5000)
            }
        } catch (e: Exception) {
            Log.e(TAG, "UDP Broadcast failed", e)
        }
    }

    fun stopBroadcasting() {
        nsdManager?.unregisterService(registrationListener)
    }
}
