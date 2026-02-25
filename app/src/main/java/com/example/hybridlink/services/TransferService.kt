package com.example.hybridlink.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import com.example.hybridlink.data.TransferEngine
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import javax.inject.Inject

@AndroidEntryPoint
class TransferService : LifecycleService() {

    @Inject
    lateinit var transferEngine: TransferEngine

    private lateinit var notificationManager: NotificationManager

    override fun onCreate() {
        super.onCreate()
        notificationManager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)

        when (intent?.action) {
            ACTION_START -> {
                val isSending = intent.getBooleanExtra(EXTRA_IS_SENDING, true)
                // In a real app, we would pass file path here
                startForeground(NOTIFICATION_ID, createNotification(0))
                observeProgress()
            }
            ACTION_STOP -> {
                transferEngine.cancelTransfer()
                stopSelf()
            }
        }

        return START_STICKY
    }

    private fun observeProgress() {
        transferEngine.progress.onEach { progress ->
            notificationManager.notify(NOTIFICATION_ID, createNotification((progress * 100).toInt()))
        }.launchIn(lifecycleScope)
    }

    private fun createNotification(progress: Int): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("HybridLink Transfer")
            .setContentText("Transferring: $progress%")
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setProgress(100, progress, false)
            .setOngoing(true)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "File Transfer",
                NotificationManager.IMPORTANCE_LOW
            )
            notificationManager.createNotificationChannel(channel)
        }
    }

    companion object {
        const val CHANNEL_ID = "transfer_channel"
        const val NOTIFICATION_ID = 1
        const val ACTION_START = "com.example.hybridlink.services.action.START"
        const val ACTION_STOP = "com.example.hybridlink.services.action.STOP"
        const val EXTRA_IS_SENDING = "extra_is_sending"
    }
}
