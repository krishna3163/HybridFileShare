package com.example.hybridlink.transfer

import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import java.io.DataOutputStream
import java.io.File
import java.io.FileInputStream
import java.net.Socket

/**
 * FileBlockSender — reads files from disk in 1MB chunks and sends them
 * across multiple TCP transfer channels simultaneously.
 *
 * Architecture (mirrors HybridFileXfer-main/SendFileCall):
 *  - One coroutine reads files into FileBlock chunks → Channel<FileBlock>
 *  - N sender coroutines (one per NIC/socket) pull blocks and write to their socket
 */
class FileBlockSender(
    private val sockets: List<Socket>,
    private val channelNames: List<String>
) {
    companion object {
        private const val TAG = "FileBlockSender"
    }

    data class TransferResult(
        val totalBytes: Long,
        val totalFiles: Int,
        val elapsedMs: Long,
        val perChannelBytes: Map<String, Long>
    )

    /**
     * Send a list of files across all connected channels.
     * @param files List of File objects to send
     * @param onProgress Called with (currentFile, bytesSent, totalBytes)
     * @param onSpeed Called every second with per-channel speeds
     */
    suspend fun sendFiles(
        files: List<File>,
        onProgress: ((String, Long, Long) -> Unit)? = null,
        onSpeed: ((Map<String, Long>) -> Unit)? = null
    ): TransferResult = withContext(Dispatchers.IO) {
        val blockQueue = Channel<FileBlock>(capacity = 64) // buffered queue
        val startTime = System.currentTimeMillis()
        val perChannelBytes = mutableMapOf<String, Long>()
        channelNames.forEach { perChannelBytes[it] = 0L }

        // Producer: read all files into FileBlocks
        val producerJob = launch {
            var fileIndex = 0
            for (file in files) {
                if (file.isDirectory) {
                    blockQueue.send(
                        FileBlock(fileIndex, 0, file.name, null, 0, file.lastModified(), false)
                    )
                    fileIndex++
                    continue
                }

                val fileSize = file.length()
                val totalBlocks = ((fileSize + FileBlock.BLOCK_SIZE - 1) / FileBlock.BLOCK_SIZE).toInt().coerceAtLeast(1)
                val fis = FileInputStream(file)

                for (blockIdx in 0 until totalBlocks) {
                    val readSize = minOf(FileBlock.BLOCK_SIZE.toLong(), fileSize - blockIdx.toLong() * FileBlock.BLOCK_SIZE).toInt()
                    val data = ByteArray(readSize)
                    var bytesRead = 0
                    while (bytesRead < readSize) {
                        val n = fis.read(data, bytesRead, readSize - bytesRead)
                        if (n == -1) break
                        bytesRead += n
                    }

                    blockQueue.send(
                        FileBlock(fileIndex, blockIdx, file.name, data, fileSize, file.lastModified(), true)
                    )
                    onProgress?.invoke(file.name, (blockIdx + 1).toLong() * FileBlock.BLOCK_SIZE, fileSize)
                }
                fis.close()
                fileIndex++
            }
            // Send END_POINT sentinel for each channel
            repeat(sockets.size) {
                blockQueue.send(FileBlock.END_POINT)
            }
            blockQueue.close()
        }

        // Consumer: N sender coroutines, one per socket
        val senderJobs = sockets.mapIndexed { idx, socket ->
            launch {
                val dos = DataOutputStream(socket.getOutputStream())
                val name = channelNames.getOrElse(idx) { "Channel_$idx" }

                try {
                    for (block in blockQueue) {
                        if (block.fileIndex == -1) {
                            // Sentinel block
                            dos.writeShort(TransferIdentifiers.EOF.toInt())
                            dos.flush()
                            break
                        }

                        // Write protocol header
                        dos.writeShort(
                            if (block.isFile) TransferIdentifiers.FILE.toInt()
                            else TransferIdentifiers.FOLDER.toInt()
                        )
                        dos.writeInt(block.fileIndex)
                        dos.writeUTF(block.path)
                        dos.writeLong(block.lastModified)

                        if (!block.isFile) continue

                        dos.writeLong(block.totalSize)
                        dos.writeInt(block.blockIndex)
                        dos.writeInt(block.getLength())

                        // Write data
                        block.data?.let { data ->
                            dos.write(data)
                            perChannelBytes[name] = (perChannelBytes[name] ?: 0L) + data.size
                        }
                        dos.flush()
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Sender error on $name: ${e.message}")
                    throw e
                }
            }
        }

        producerJob.join()
        senderJobs.forEach { it.join() }

        val totalBytes = perChannelBytes.values.sum()
        val elapsed = System.currentTimeMillis() - startTime

        TransferResult(totalBytes, files.size, elapsed, perChannelBytes)
    }
}
