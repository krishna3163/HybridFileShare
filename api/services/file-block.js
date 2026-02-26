/**
 * FileBlock — represents a 1MB chunk of a file being transferred.
 * Mirrors the Java FileBlock class from HybridFileXfer-main.
 */

const BLOCK_SIZE = 1024 * 1024; // 1MB

class FileBlock {
    /**
     * @param {number} fileIndex - Index of the file in the transfer batch
     * @param {number} blockIndex - Index of this block within the file
     * @param {string} path - Relative path of the file
     * @param {Buffer|null} data - The raw bytes (up to 1MB)
     * @param {number} totalSize - Total size of the entire file
     * @param {number} lastModified - Timestamp (ms) of last modification
     * @param {boolean} isFile - true = file, false = directory
     */
    constructor(fileIndex, blockIndex, path, data, totalSize, lastModified, isFile = true) {
        this.fileIndex = fileIndex;
        this.blockIndex = blockIndex;
        this.path = path;
        this.data = data;
        this.totalSize = totalSize;
        this.lastModified = lastModified;
        this.isFile = isFile;
    }

    getLength() {
        return this.data ? this.data.length : 0;
    }

    getStartPosition() {
        return this.blockIndex * BLOCK_SIZE;
    }
}

// Sentinel blocks (special fileIndex = -1)
FileBlock.END_POINT = new FileBlock(-1, 0, '', null, 0, 0);
FileBlock.INTERRUPT = new FileBlock(-1, 1, '', null, 0, 0);
FileBlock.READ_ERROR = new FileBlock(-1, 2, '', null, 0, 0);
FileBlock.WRITE_ERROR = new FileBlock(-1, 3, '', null, 0, 0);

// Transfer protocol identifiers (matches Java TransferIdentifiers)
const TransferIdentifiers = {
    FILE: 0x0001,
    FOLDER: 0x0002,
    EOF: 0x0010,
    END_OF_INTERRUPTED: 0x0011,
    END_OF_READ_ERROR: 0x0012,
    END_OF_WRITE_ERROR: 0x0013,
};

// Controller protocol identifiers (matches Java ControllerIdentifiers)
const ControllerIdentifiers = {
    LIST_FILES: 0x01,
    SEND_FILES: 0x02,
    RECEIVE_FILES: 0x03,
    MKDIR: 0x04,
    DELETE: 0x05,
    SHUTDOWN: 0xFF,
};

module.exports = { FileBlock, TransferIdentifiers, ControllerIdentifiers, BLOCK_SIZE };
