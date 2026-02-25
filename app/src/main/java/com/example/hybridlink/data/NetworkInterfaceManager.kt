package com.example.hybridlink.data

import android.util.Log
import java.net.Inet4Address
import java.net.NetworkInterface
import java.net.SocketException
import java.util.Collections

data class ActiveInterface(
    val name: String,
    val ipAddress: String,
    val type: InterfaceType
)

enum class InterfaceType {
    WIFI_MAIN, // wlan0
    WIFI_WFA,  // wlan1 (dual wifi acceleration)
    USB_TETHER,// rndis0 / usb0
    ETHERNET,  // eth0
    USB_ADB,   // 127.0.0.1 (ADB Forwarded)
    UNKNOWN
}

class NetworkInterfaceManager {

    fun getActiveInterfaces(): List<ActiveInterface> {
        val interfaces = mutableListOf<ActiveInterface>()
        
        // Add ADB loopback interface explicitly
        interfaces.add(ActiveInterface("USB_ADB", "127.0.0.1", InterfaceType.USB_ADB))

        try {
            val networkInterfaces = Collections.list(NetworkInterface.getNetworkInterfaces())
            for (networkInterface in networkInterfaces) {
                // Ignore down interfaces or loopbacks (we already manually added ADB loopback)
                if (!networkInterface.isUp || networkInterface.isLoopback) continue

                val ipAddresses = Collections.list(networkInterface.inetAddresses)
                for (address in ipAddresses) {
                    if (!address.isLoopbackAddress && address is Inet4Address) {
                        val name = networkInterface.name
                        val type = categorizeInterface(name)
                        interfaces.add(ActiveInterface(name, address.hostAddress ?: "", type))
                        Log.d("NetworkInterface", "Found active interface: $name (${address.hostAddress})")
                    }
                }
            }
        } catch (ex: SocketException) {
            Log.e("NetworkInterface", "Error enumerating interfaces: ${ex.message}")
        }
        
        return interfaces
    }

    private fun categorizeInterface(name: String): InterfaceType {
        return when {
            name.startsWith("wlan0") -> InterfaceType.WIFI_MAIN
            name.startsWith("wlan1") || name.startsWith("p2p") -> InterfaceType.WIFI_WFA
            name.startsWith("rndis") || name.startsWith("usb") -> InterfaceType.USB_TETHER
            name.startsWith("eth") -> InterfaceType.ETHERNET
            else -> InterfaceType.UNKNOWN
        }
    }
}
