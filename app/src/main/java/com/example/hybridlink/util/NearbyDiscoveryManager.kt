package com.example.hybridlink.util

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.util.Log
import android.provider.Settings
import android.os.Build
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

data class DiscoveredDevice(
    val id: String,
    val name: String,
    val host: String,
    val port: Int,
    val platform: String = "unknown",
    val lastSeen: Long = System.currentTimeMillis()
)

class NearbyDiscoveryManager(private val context: Context) {
    private val nsdManager = context.getSystemService(Context.NSD_SERVICE) as NsdManager
    private val serviceType = "_hybridfileshare._tcp"
    
    private val _discoveredDevices = MutableStateFlow<List<DiscoveredDevice>>(emptyList())
    val discoveredDevices = _discoveredDevices.asStateFlow()

    private var registrationListener: NsdManager.RegistrationListener? = null
    private var discoveryListener: NsdManager.DiscoveryListener? = null

    fun startAdvertising(deviceName: String, port: Int) {
        stopAdvertising()
        
        val deviceId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "android-dev"
        
        val serviceInfo = NsdServiceInfo().apply {
            this.serviceName = deviceName
            this.serviceType = this@NearbyDiscoveryManager.serviceType
            this.setPort(port)
            // TXT records for unified metadata
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                this.setAttribute("deviceId", deviceId)
                this.setAttribute("platform", "android")
                this.setAttribute("version", "1.0.0")
                this.setAttribute("deviceName", deviceName)
            }
        }

        registrationListener = object : NsdManager.RegistrationListener {
            override fun onServiceRegistered(NsdServiceInfo: NsdServiceInfo) {
                Log.d("NSD", "Service Registered: ${NsdServiceInfo.serviceName}")
            }

            override fun onRegistrationFailed(arg0: NsdServiceInfo, arg1: Int) {}
            override fun onServiceUnregistered(arg0: NsdServiceInfo) {}
            override fun onUnregistrationFailed(arg0: NsdServiceInfo, arg1: Int) {}
        }

        nsdManager.registerService(serviceInfo, NsdManager.PROTOCOL_DNS_SD, registrationListener)
    }

    fun stopAdvertising() {
        registrationListener?.let {
            try {
                nsdManager.unregisterService(it)
            } catch (e: Exception) {
                Log.e("NSD", "Unregister failed", e)
            }
        }
        registrationListener = null
    }

    fun startDiscovery() {
        stopDiscovery()
        
        discoveryListener = object : NsdManager.DiscoveryListener {
            override fun onDiscoveryStarted(regType: String) {
                Log.d("NSD", "Discovery started")
            }

            override fun onServiceFound(service: NsdServiceInfo) {
                if (service.serviceType.contains(serviceType)) {
                    nsdManager.resolveService(service, object : NsdManager.ResolveListener {
                        override fun onResolveFailed(serviceInfo: NsdServiceInfo, errorCode: Int) {
                            Log.e("NSD", "Resolve failed $errorCode")
                        }

                        override fun onServiceResolved(serviceInfo: NsdServiceInfo) {
                            val deviceId = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                                serviceInfo.attributes["deviceId"]?.let { String(it) } ?: serviceInfo.serviceName
                            } else {
                                serviceInfo.serviceName
                            }
                            
                            val platform = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                                serviceInfo.attributes["platform"]?.let { String(it) } ?: "unknown"
                            } else {
                                "unknown"
                            }

                            val device = DiscoveredDevice(
                                id = deviceId,
                                name = serviceInfo.serviceName,
                                host = serviceInfo.host.hostAddress ?: "",
                                port = serviceInfo.port,
                                platform = platform
                            )
                            _discoveredDevices.update { current ->
                                (current.filter { it.id != device.id } + device)
                            }
                        }
                    })
                }
            }

            override fun onServiceLost(service: NsdServiceInfo) {
                // Since we don't have the ID here, we still filter by name for removal
                _discoveredDevices.update { current ->
                    current.filter { it.name != service.serviceName }
                }
            }

            override fun onDiscoveryStopped(serviceType: String) {}
            override fun onStartDiscoveryFailed(serviceType: String, errorCode: Int) {
                nsdManager.stopServiceDiscovery(this)
            }
            override fun onStopDiscoveryFailed(serviceType: String, errorCode: Int) {
                nsdManager.stopServiceDiscovery(this)
            }
        }

        nsdManager.discoverServices(serviceType, NsdManager.PROTOCOL_DNS_SD, discoveryListener)
    }

    fun stopDiscovery() {
        discoveryListener?.let {
            try {
                nsdManager.stopServiceDiscovery(it)
            } catch (e: Exception) {
                Log.e("NSD", "Stop discovery failed", e)
            }
        }
        discoveryListener = null
        _discoveredDevices.value = emptyList()
    }
}
