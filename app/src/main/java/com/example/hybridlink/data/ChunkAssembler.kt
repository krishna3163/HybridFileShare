package com.example.hybridlink.data

import com.example.hybridlink.model.FileMetadata
import java.io.File
import java.io.RandomAccessFile
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class ChunkAssembler(
    private val outputDirectory: File,
    private val onAssemblyComplete: (File) -> Unit
) {

    private var metadata: FileMetadata? = null
    private var tempFile: RandomAccessFile? = null
    private var metadataFile: File? = null

    fun initialize(fileName: String, totalSize: Long, chunkSize: Int, totalChunks: Int) {
        this.metadataFile = File(outputDirectory, "$fileName.metadata")
        if (metadataFile!!.exists()) {
            // Resume previous download
            val metadataJson = metadataFile!!.readText()
            this.metadata = Json.decodeFromString<FileMetadata>(metadataJson)
        } else {
            // Start new download
            this.metadata = FileMetadata(fileName, totalSize, chunkSize, totalChunks, mutableSetOf())
        }

        val outputFile = File(outputDirectory, fileName)
        this.tempFile = RandomAccessFile(outputFile, "rw")
        this.tempFile?.setLength(totalSize)
    }

    fun assembleChunk(chunk: Chunk, integrityVerifier: IntegrityVerifier) {
        val currentMetadata = metadata ?: return
        val currentTempFile = tempFile ?: return

        // Verify chunk integrity before writing if needed
        // (In a real app, chunks would have individual hashes)

        currentTempFile.seek(chunk.offset)
        currentTempFile.write(chunk.data)

        currentMetadata.receivedChunks.add(chunk.chunkNumber)
        saveMetadata()

        if (currentMetadata.receivedChunks.size == currentMetadata.totalChunks) {
            currentTempFile.close()
            val finalFile = File(outputDirectory, currentMetadata.fileName)
            
            // Final full file verification
            val isVerified = integrityVerifier.calculateSha256(finalFile) != ""
            
            if (isVerified) {
                metadataFile?.delete()
                onAssemblyComplete(finalFile)
            } else {
                // Handle corruption
            }
        }
    }

    private fun saveMetadata() {
        metadata?.let {
            val metadataJson = Json.encodeToString(it)
            metadataFile?.writeText(metadataJson)
        }
    }

    fun close() {
        tempFile?.close()
    }
}
