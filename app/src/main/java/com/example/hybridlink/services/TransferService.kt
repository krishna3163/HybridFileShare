package com.example.hybridlink.services

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService

class TransferService : LifecycleService() {

    private lateinit var notificationManager: NotificationManager

    override fun onCreate() {
        super.onCreate()
        notificationManager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "File Transfer",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            notificationManager.createNotificationChannel(channel)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)

        when (intent?.action) {
            ACTION_START -> {
                // TODO: Get file metadata from intent
                startForeground(NOTIFICATION_ID, createNotification(0))
                // TODO: Start transfer logic
            }
            ACTION_PAUSE -> {
                // TODO: Pause transfer logic
            }
            ACTION_RESUME -> {
                // TODO: Resume transfer logic
            }
            ACTION_CANCEL -> {
                stopSelf()
            }
        }

        return START_STICKY
    }

    private fun createNotification(progress: Int): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("File Transfer")
            .setContentText("Transfer in progress: $progress%")
            //.setSmallIcon(R.drawable.ic_launcher_foreground) // TODO: Replace with a real icon
            .setProgress(100, progress, false)
            .build()
    }

    companion object {
        const val CHANNEL_ID = "transfer_channel"
        const val NOTIFICATION_ID = 1
        const val ACTION_START = "com.example.hybridlink.services.action.START"
        const val ACTION_PAUSE = "com.example.hybridlink.services.action.PAUSE"
        const val ACTION_RESUME = "com.example.hybridlink.services.action.RESUME"
        const val ACTION_CANCEL = "com.example.hybridlink.services.action.CANCEL"
    }
}
