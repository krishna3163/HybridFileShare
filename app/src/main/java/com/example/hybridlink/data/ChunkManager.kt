package com.example.hybridlink.data

import com.example.hybridlink.model.FileMetadata
import java.io.File
import java.io.RandomAccessFile
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.atomic.AtomicBoolean

class ChunkManager(
    private val saveDir: File,
    private val fileMetadata: FileMetadata,
    private val chunkSize: Long = 4 * 1024 * 1024 // 4MB
) {
    private lateinit var randomAccessFile: RandomAccessFile
    private val _bytesReceived = MutableStateFlow(0L)
    val bytesReceived = _bytesReceived.asStateFlow()
    val isComplete = AtomicBoolean(false)

    init {
        val targetFile = File(saveDir, fileMetadata.fileName)
        randomAccessFile = RandomAccessFile(targetFile, "rw")
        randomAccessFile.setLength(fileMetadata.totalSize)
    }

    @Synchronized
    fun writeChunk(chunkId: Int, data: ByteArray) {
        val offset = chunkId.toLong() * chunkSize
        randomAccessFile.seek(offset)
        randomAccessFile.write(data)
        
        fileMetadata.receivedChunks.add(chunkId)
        _bytesReceived.value += data.size

        if (_bytesReceived.value >= fileMetadata.totalSize) {
            isComplete.set(true)
            randomAccessFile.close()
        }
    }

    @Synchronized
    fun readChunk(chunkId: Int, dataBuffer: ByteArray): Int {
        val offset = chunkId.toLong() * chunkSize
        randomAccessFile.seek(offset)
        return randomAccessFile.read(dataBuffer)
    }

    fun cleanup() {
        try {
            randomAccessFile.close()
        } catch (e: Exception) {}
    }
}
