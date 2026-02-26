package com.example.hybridlink.ui.viewmodels

import android.app.ActivityManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.net.ConnectivityManager
import android.os.IBinder
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.hybridlink.R
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import rikka.shizuku.Shizuku
import top.weixiansen574.async.BackstageTask
import top.weixiansen574.hybridfilexfer.Config
import top.weixiansen574.hybridfilexfer.IOService
import top.weixiansen574.hybridfilexfer.aidl.IIOService
import top.weixiansen574.hybridfilexfer.core.bean.ServerNetInterface
import top.weixiansen574.hybridfilexfer.droidcore.HFXServer
import top.weixiansen574.hybridfilexfer.droidcore.StartServerTask
import top.weixiansen574.hybridfilexfer.droidcore.callback.StartServerCallback
import com.example.hybridlink.util.NearbyDiscoveryManager
import com.example.hybridlink.util.NearbyWebServer
import com.example.hybridlink.util.DiscoveredDevice
import java.net.Inet4Address
import java.net.InetAddress
import java.net.NetworkInterface
import java.util.Enumeration
import javax.inject.Inject

data class NetworkInterfaceItem(
    val name: String,
    val address: String,
    val inetAddress: InetAddress,
    var isEnabled: Boolean = true,
    var state: String = "Idle"
)

@HiltViewModel
class MainViewModel @Inject constructor(
    @ApplicationContext private val context: Context
) : ViewModel(), ServiceConnection {

    var server by mutableStateOf<HFXServer?>(null)
        private set

    var isServerRunning by mutableStateOf(false)
        private set

    var serverStatusText by mutableStateOf("Ready to Start")
        private set

    var accessMode by mutableStateOf("NORMAL")
    
    val networkInterfaces = mutableStateListOf<NetworkInterfaceItem>()

    private val config = Config.getInstance(context)
    
    // Nearby Features
    private val discoveryManager = NearbyDiscoveryManager(context)
    private var webServer: NearbyWebServer? = null
    
    val discoveredDevices = discoveryManager.discoveredDevices
    var isWebShareEnabled by mutableStateOf(false)
        private set

    init {
        refreshInterfaces()
    }

    override fun onCleared() {
        super.onCleared()
        discoveryManager.stopDiscovery()
        discoveryManager.stopAdvertising()
        webServer?.stop()
    }

    fun refreshInterfaces() {
        viewModelScope.launch {
            networkInterfaces.clear()
            // Add loopback/ADB channel
            networkInterfaces.add(
                NetworkInterfaceItem(
                    "USB_ADB",
                    "127.0.0.1",
                    InetAddress.getByName("127.0.0.1"),
                    state = "Ready"
                )
            )

            try {
                val interfaces: Enumeration<NetworkInterface> = NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val networkInterface = interfaces.nextElement()
                    val addresses = networkInterface.inetAddresses
                    while (addresses.hasMoreElements()) {
                        val address = addresses.nextElement()
                        if (!address.isLoopbackAddress && address is Inet4Address && 
                            !networkInterface.displayName.startsWith("rmnet_data")) {
                            
                            val isTun = networkInterface.displayName.startsWith("tun")
                            networkInterfaces.add(
                                NetworkInterfaceItem(
                                    networkInterface.displayName,
                                    address.hostAddress ?: "",
                                    address,
                                    isEnabled = !isTun,
                                    state = "Ready"
                                )
                            )
                        }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun toggleServer() {
        if (isServerRunning) {
            stopServer()
        } else {
            startServer()
        }
    }

    private fun startServer() {
        val selected = networkInterfaces.filter { it.isEnabled }.map {
            ServerNetInterface(it.name, it.inetAddress, null)
        }

        if (selected.isEmpty()) {
            serverStatusText = "No network interfaces selected"
            return
        }

        serverStatusText = "Initializing..."
        
        if (accessMode == "SHIZUKU" || accessMode == "ROOT") {
            if (!Shizuku.pingBinder()) {
                serverStatusText = "Shizuku not running"
                return
            }
            Shizuku.bindUserService(IOService.getUserServiceArgs(context), this)
        } else {
            val intent = Intent(context, top.weixiansen574.hybridfilexfer.IOService::class.java)
            context.bindService(intent, this, Context.BIND_AUTO_CREATE)
        }
    }

    private fun stopServer() {
        serverStatusText = "Stopping..."
        val currentServer = server
        if (currentServer == null) {
            isServerRunning = false
            serverStatusText = "Stopped"
            return
        }

        if (HFXServer.instance == null) {
            currentServer.closeServerSocket()
            cleanupServer()
        } else {
            currentServer.disconnect(object : BackstageTask.BaseEventHandler {
                override fun onComplete() {
                    cleanupServer()
                }
            })
        }
    }

    private fun cleanupServer() {
        try {
            if (accessMode == "SHIZUKU" || accessMode == "ROOT") {
                Shizuku.unbindUserService(IOService.getUserServiceArgs(context), this, true)
            } else {
                context.unbindService(this)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        server = null
        HFXServer.instance = null
        isServerRunning = false
        serverStatusText = "Stopped"
    }

    override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
        val iioService = IIOService.Stub.asInterface(service)
        val hfxServer = HFXServer(iioService)
        server = hfxServer

        val selectedSpecs = networkInterfaces.filter { it.isEnabled }.map {
            ServerNetInterface(it.name, it.inetAddress, null)
        }

        val callback = object : StartServerCallback {
            override fun onBindFailed(port: Int) {
                serverStatusText = "Bind Failed (Port $port)"
                isServerRunning = false
            }

            override fun onStatedServer() {
                isServerRunning = true
                serverStatusText = "Waiting for Connection..."
            }

            override fun onAccepted(name: String) {
                updateInterfaceState(name, "Connected")
            }

            override fun onAcceptFailed(name: String) {
                updateInterfaceState(name, "Failed")
            }

            override fun onPcOOM() {
                serverStatusText = "PC Out of Memory"
                stopServer()
            }

            override fun onMeOOM(created: Int, total: Int) {
                serverStatusText = "OOM ($created/$total MB)"
                stopServer()
            }

            override fun onConnectSuccess() {
                serverStatusText = "Active"
                HFXServer.instance = server
            }

            override fun onError(th: Throwable?) {
                serverStatusText = "Error: ${th?.message}"
                stopServer()
            }
        }

        StartServerTask(
            callback,
            hfxServer,
            config.serverPort,
            selectedSpecs,
            config.localBufferCount,
            config.remoteBufferCount
        ).execute()
    }

    override fun onServiceDisconnected(name: ComponentName?) {
        isServerRunning = false
        serverStatusText = "Service Disconnected"
    }

    private fun updateInterfaceState(name: String, state: String) {
        val index = networkInterfaces.indexOfFirst { it.name == name }
        if (index != -1) {
            networkInterfaces[index] = networkInterfaces[index].copy(state = state)
        }
    }

    fun getAvailableMemoryMB(): Long {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        val totalMemoryMB = memoryInfo.totalMem / (1024 * 1024)
        val availableMemoryMB = memoryInfo.availMem / (1024 * 1024)
        return (availableMemoryMB - (totalMemoryMB * 0.05)).toLong()
    }

    fun toggleWebShare() {
        if (isWebShareEnabled) {
            webServer?.stop()
            discoveryManager.stopAdvertising()
            isWebShareEnabled = false
        } else {
            webServer = NearbyWebServer(context, server)
            webServer?.start(8080)
            discoveryManager.startAdvertising(android.os.Build.MODEL, config.serverPort)
            isWebShareEnabled = true
        }
    }

    fun startDiscovery() {
        discoveryManager.startDiscovery()
    }

    fun stopDiscovery() {
        discoveryManager.stopDiscovery()
    }
}
