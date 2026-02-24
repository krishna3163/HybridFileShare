package com.example.hybridlink.model

import kotlinx.serialization.Serializable

@Serializable
data class FileMetadata(
    val fileName: String,
    val totalSize: Long,
    val chunkSize: Int,
    val totalChunks: Int,
    val receivedChunks: MutableSet<Int>
)
