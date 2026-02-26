package com.example.hybridlink.transfer

import android.util.Log
import kotlinx.coroutines.*
import java.io.DataInputStream
import java.io.File
import java.io.FileOutputStream
import java.io.RandomAccessFile
import java.net.Socket

/**
 * FileBlockReceiver — receives file blocks from multiple TCP channels
 * and reassembles them into complete files on disk.
 *
 * Architecture (mirrors HybridFileXfer-main/ReceiveFileCall + WriteFileCall):
 *  - N receiver coroutines (one per socket) read blocks from their socket
 *  - Blocks are written to disk at the correct offset (blockIndex * BLOCK_SIZE)
 */
class FileBlockReceiver(
    private val sockets: List<Socket>,
    private val channelNames: List<String>,
    private val destDir: File
) {
    companion object {
        private const val TAG = "FileBlockReceiver"
    }

    data class ReceiveResult(
        val totalBytes: Long,
        val totalFiles: Int,
        val elapsedMs: Long,
        val perChannelBytes: Map<String, Long>
    )

    /**
     * Receive files from all connected channels into destDir.
     * @param onProgress Called with (currentFile, bytesReceived, totalSize)
     */
    suspend fun receiveFiles(
        onProgress: ((String, Long, Long) -> Unit)? = null
    ): ReceiveResult = withContext(Dispatchers.IO) {
        val startTime = System.currentTimeMillis()
        val perChannelBytes = mutableMapOf<String, Long>()
        channelNames.forEach { perChannelBytes[it] = 0L }

        // Track open files by fileIndex for random-access writing
        val openFiles = mutableMapOf<Int, RandomAccessFile>()
        val filePaths = mutableMapOf<Int, String>()
        var totalFiles = 0

        if (!destDir.exists()) destDir.mkdirs()

        // One receiver coroutine per socket
        val receiverJobs = sockets.mapIndexed { idx, socket ->
            launch {
                val dis = DataInputStream(socket.getInputStream())
                val name = channelNames.getOrElse(idx) { "Channel_$idx" }

                try {
                    while (true) {
                        val type = dis.readShort()

                        // Check for sentinel types
                        if (type == TransferIdentifiers.EOF ||
                            type == TransferIdentifiers.END_OF_INTERRUPTED ||
                            type == TransferIdentifiers.END_OF_READ_ERROR ||
                            type == TransferIdentifiers.END_OF_WRITE_ERROR
                        ) {
                            Log.i(TAG, "Channel $name received end signal: 0x${type.toString(16)}")
                            break
                        }

                        val fileIndex = dis.readInt()
                        val path = dis.readUTF()
                        val lastModified = dis.readLong()

                        if (type == TransferIdentifiers.FOLDER) {
                            // Create directory
                            val dir = File(destDir, path)
                            dir.mkdirs()
                            synchronized(filePaths) {
                                filePaths[fileIndex] = path
                                totalFiles++
                            }
                            continue
                        }

                        // FILE type
                        val totalSize = dis.readLong()
                        val blockIndex = dis.readInt()
                        val blockLength = dis.readInt()

                        // Read data
                        val data = ByteArray(blockLength)
                        var bytesRead = 0
                        while (bytesRead < blockLength) {
                            val n = dis.read(data, bytesRead, blockLength - bytesRead)
                            if (n == -1) throw Exception("Unexpected end of stream")
                            bytesRead += n
                        }

                        // Write to file at correct offset
                        synchronized(openFiles) {
                            if (!openFiles.containsKey(fileIndex)) {
                                val outFile = File(destDir, path)
                                outFile.parentFile?.mkdirs()
                                openFiles[fileIndex] = RandomAccessFile(outFile, "rw")
                                openFiles[fileIndex]!!.setLength(totalSize)
                                filePaths[fileIndex] = path
                                totalFiles++
                            }
                        }

                        val raf = synchronized(openFiles) { openFiles[fileIndex]!! }
                        val writeOffset = blockIndex.toLong() * FileBlock.BLOCK_SIZE
                        synchronized(raf) {
                            raf.seek(writeOffset)
                            raf.write(data)
                        }

                        perChannelBytes[name] = (perChannelBytes[name] ?: 0L) + blockLength
                        onProgress?.invoke(path, writeOffset + blockLength, totalSize)
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Receiver error on $name: ${e.message}")
                    throw e
                }
            }
        }

        receiverJobs.forEach { it.join() }

        // Close all open files
        synchronized(openFiles) {
            openFiles.values.forEach {
                try { it.close() } catch (e: Exception) { }
            }
        }

        val totalBytes = perChannelBytes.values.sum()
        val elapsed = System.currentTimeMillis() - startTime

        ReceiveResult(totalBytes, totalFiles, elapsed, perChannelBytes)
    }
}
