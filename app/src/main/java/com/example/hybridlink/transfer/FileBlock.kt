package com.example.hybridlink.transfer

/**
 * FileBlock — represents a 1MB chunk of a file being transferred.
 * Direct port of the Java FileBlock from HybridFileXfer-main.
 */
data class FileBlock(
    val fileIndex: Int,
    val blockIndex: Int,
    val path: String,
    val data: ByteArray?,
    val totalSize: Long,
    val lastModified: Long,
    val isFile: Boolean = true
) {
    fun getLength(): Int = data?.size ?: 0
    fun getStartPosition(): Long = blockIndex.toLong() * BLOCK_SIZE

    companion object {
        const val BLOCK_SIZE = 1024 * 1024 // 1MB

        // Sentinel blocks (fileIndex = -1)
        val END_POINT = FileBlock(-1, 0, "", null, 0, 0)
        val INTERRUPT = FileBlock(-1, 1, "", null, 0, 0)
        val READ_ERROR = FileBlock(-1, 2, "", null, 0, 0)
        val WRITE_ERROR = FileBlock(-1, 3, "", null, 0, 0)
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is FileBlock) return false
        return fileIndex == other.fileIndex && blockIndex == other.blockIndex
    }

    override fun hashCode(): Int = 31 * fileIndex + blockIndex
}

/**
 * Transfer protocol identifiers matching the Java/Node.js protocol.
 */
object TransferIdentifiers {
    const val FILE: Short = 0x0001
    const val FOLDER: Short = 0x0002
    const val EOF: Short = 0x0010
    const val END_OF_INTERRUPTED: Short = 0x0011
    const val END_OF_READ_ERROR: Short = 0x0012
    const val END_OF_WRITE_ERROR: Short = 0x0013
}
