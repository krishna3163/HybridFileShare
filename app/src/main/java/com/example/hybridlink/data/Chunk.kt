package com.example.hybridlink.data

data class Chunk(
    val chunkNumber: Int,
    val offset: Long,
    val data: ByteArray
)
