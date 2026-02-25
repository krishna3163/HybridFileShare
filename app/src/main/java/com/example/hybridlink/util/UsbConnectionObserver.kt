package com.example.hybridlink.util

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.distinctUntilChanged

class UsbConnectionObserver(private val context: Context) {

    fun observe(): Flow<Status> = callbackFlow {
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                if (intent.action == "android.hardware.usb.action.USB_STATE") {
                    val connected = intent.extras?.getBoolean("connected") ?: false
                    trySend(if (connected) Status.Connected else Status.Disconnected)
                }
            }
        }

        context.registerReceiver(receiver, IntentFilter("android.hardware.usb.action.USB_STATE"))
        
        awaitClose {
            context.unregisterReceiver(receiver)
        }
    }.distinctUntilChanged()

    enum class Status {
        Connected, Disconnected
    }
}
