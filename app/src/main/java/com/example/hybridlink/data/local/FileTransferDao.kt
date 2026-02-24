package com.example.hybridlink.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface FileTransferDao {
    @Insert
    suspend fun insertFileMetadata(fileMetadata: FileMetadata): Long

    @Update
    suspend fun updateFileMetadata(fileMetadata: FileMetadata)

    @Query("SELECT * FROM file_metadata WHERE id = :id")
    fun getFileMetadata(id: Long): Flow<FileMetadata?>

    @Query("SELECT * FROM file_metadata")
    fun getAllFileMetadata(): Flow<List<FileMetadata>>
}
