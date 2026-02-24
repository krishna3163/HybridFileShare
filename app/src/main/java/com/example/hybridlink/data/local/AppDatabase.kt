package com.example.hybridlink.data.local

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [FileMetadata::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun fileTransferDao(): FileTransferDao
}
