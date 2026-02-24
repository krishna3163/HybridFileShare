package com.example.hybridlink.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "file_metadata")
data class FileMetadata(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val fileName: String,
    val fileSize: Long,
    val sha256: String,
    val transferStatus: String,
    val isSender: Boolean
)
