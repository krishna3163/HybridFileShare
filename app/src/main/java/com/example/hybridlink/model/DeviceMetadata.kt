package com.example.hybridlink.model

import kotlinx.serialization.Serializable

@Serializable
data class DeviceMetadata(
    val id: String,
    val name: String,
    val osType: String,
    val availableTransports: List<String>,
    val batteryLevel: Int = -1,
    val trustStatus: String = "untrusted"
)
