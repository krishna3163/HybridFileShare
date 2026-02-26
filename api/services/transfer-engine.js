/**
 * TransferEngine — the main orchestrator for real file transfers.
 * 
 * Architecture:
 *  - Control Channel: TCP on port 5740, exchanges commands (list files, send, receive)
 *  - Transfer Channels: N TCP connections (one per NIC), carry raw file block data
 *  - Protocol: Binary framed messages matching the HybridFileXfer Java protocol
 */

const net = require('net');
const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');
const { FileBlock, TransferIdentifiers, ControllerIdentifiers, BLOCK_SIZE } = require('./file-block');
const { TransferConnection } = require('./transfer-connection');
const { SpeedMonitor } = require('./speed-monitor');

class TransferEngine extends EventEmitter {
    constructor(options = {}) {
        super();
        this.controlPort = options.controlPort || 5740;
        this.homeDir = options.homeDir || process.cwd();
        this.controlServer = null;
        this.controlSocket = null;
        this.transferConnections = [];
        this.speedMonitor = null;
        this.state = 'idle'; // idle | waiting | connected | transferring
        this.transferProgress = null;
    }

    /**
     * Start the control channel TCP server.
     */
    startServer() {
        return new Promise((resolve, reject) => {
            this.controlServer = net.createServer((socket) => {
                this._handleControlConnection(socket);
            });

            this.controlServer.on('error', (err) => {
                if (err.code === 'EADDRINUSE') {
                    console.log(`⚠️ Control port ${this.controlPort} in use, trying ${this.controlPort + 1}`);
                    this.controlPort++;
                    this.controlServer.listen(this.controlPort);
                } else {
                    reject(err);
                }
            });

            this.controlServer.listen(this.controlPort, () => {
                this.state = 'waiting';
                console.log(`🔌 Transfer Engine listening on port ${this.controlPort}`);
                this.emit('status', { state: this.state, port: this.controlPort });
                resolve(this.controlPort);
            });
        });
    }

    /**
     * Handle an incoming control channel connection.
     */
    _handleControlConnection(socket) {
        console.log(`📡 Control channel connected from ${socket.remoteAddress}`);
        this.controlSocket = socket;
        this.state = 'connected';
        this.emit('status', { state: this.state, remoteAddress: socket.remoteAddress });

        let buffer = Buffer.alloc(0);

        socket.on('data', (chunk) => {
            buffer = Buffer.concat([buffer, chunk]);
            this._processControlBuffer(buffer, socket);
            buffer = Buffer.alloc(0); // simplified; real impl needs proper framing
        });

        socket.on('close', () => {
            console.log('🔌 Control channel disconnected');
            this.state = 'waiting';
            this.transferConnections.forEach(c => c.destroy());
            this.transferConnections = [];
            this.emit('status', { state: this.state });
        });

        socket.on('error', (err) => {
            console.error('Control channel error:', err.message);
        });
    }

    _processControlBuffer(buffer, socket) {
        // Simplified command dispatch
        if (buffer.length < 1) return;
        const cmd = buffer.readUInt8(0);

        switch (cmd) {
            case ControllerIdentifiers.LIST_FILES:
                this._handleListFiles(buffer.slice(1), socket);
                break;
            case ControllerIdentifiers.SHUTDOWN:
                this._handleShutdown(socket);
                break;
            default:
                console.log(`Unknown control command: 0x${cmd.toString(16)}`);
        }
    }

    _handleListFiles(data, socket) {
        // Read UTF path from data
        const pathStr = data.toString('utf8').trim() || this.homeDir;
        try {
            const entries = fs.readdirSync(pathStr, { withFileTypes: true });
            const files = entries.map(e => ({
                name: e.name,
                isFile: e.isFile(),
                isDirectory: e.isDirectory(),
                size: e.isFile() ? fs.statSync(path.join(pathStr, e.name)).size : 0,
                lastModified: fs.statSync(path.join(pathStr, e.name)).mtimeMs,
            }));
            const json = JSON.stringify(files);
            const buf = Buffer.alloc(4 + Buffer.byteLength(json));
            buf.writeUInt32BE(Buffer.byteLength(json), 0);
            buf.write(json, 4);
            socket.write(buf);
        } catch (err) {
            const errJson = JSON.stringify({ error: err.message });
            const buf = Buffer.alloc(4 + Buffer.byteLength(errJson));
            buf.writeUInt32BE(Buffer.byteLength(errJson), 0);
            buf.write(errJson, 4);
            socket.write(buf);
        }
    }

    _handleShutdown(socket) {
        console.log('🛑 Shutdown command received');
        this.stop();
    }

    /**
     * Send files from PC to the connected device.
     * @param {string[]} filePaths - Absolute paths of files to send
     * @param {string} remoteDir - Destination directory on the remote device
     */
    async sendFiles(filePaths, remoteDir) {
        if (this.transferConnections.length === 0) {
            throw new Error('No transfer channels connected');
        }

        this.state = 'transferring';
        this.emit('status', { state: this.state, direction: 'upload', files: filePaths.length });

        // Start speed monitor
        this.speedMonitor = new SpeedMonitor(this.transferConnections, (data) => {
            this.emit('speed', data);
        });
        this.speedMonitor.start();

        const startTime = Date.now();
        let totalBytes = 0;
        let fileIndex = 0;

        for (const filePath of filePaths) {
            const stat = fs.statSync(filePath);

            if (stat.isDirectory()) {
                // Send directory marker
                const block = new FileBlock(fileIndex, 0, path.basename(filePath), null, 0, stat.mtimeMs, false);
                await this._sendBlock(block);
                fileIndex++;
                continue;
            }

            const fileSize = stat.size;
            const totalBlocks = Math.ceil(fileSize / BLOCK_SIZE) || 1;
            const fd = fs.openSync(filePath, 'r');

            for (let blockIdx = 0; blockIdx < totalBlocks; blockIdx++) {
                const offset = blockIdx * BLOCK_SIZE;
                const readSize = Math.min(BLOCK_SIZE, fileSize - offset);
                const data = Buffer.alloc(readSize);
                fs.readSync(fd, data, 0, readSize, offset);

                const block = new FileBlock(
                    fileIndex, blockIdx, path.basename(filePath),
                    data, fileSize, stat.mtimeMs, true
                );

                // Round-robin across transfer channels
                const connIdx = blockIdx % this.transferConnections.length;
                await this._sendBlockToChannel(block, this.transferConnections[connIdx]);
                totalBytes += readSize;

                this.transferProgress = {
                    currentFile: path.basename(filePath),
                    fileIndex,
                    totalFiles: filePaths.length,
                    bytesTransferred: totalBytes,
                    blockIndex: blockIdx,
                    totalBlocks,
                };
                this.emit('progress', this.transferProgress);
            }

            fs.closeSync(fd);
            fileIndex++;
        }

        // Send EOF to all channels
        for (const conn of this.transferConnections) {
            const header = Buffer.alloc(2);
            header.writeUInt16BE(TransferIdentifiers.EOF, 0);
            conn.socket.write(header);
        }

        this.speedMonitor.stop();
        const elapsed = Date.now() - startTime;
        this.state = 'connected';

        const result = {
            direction: 'upload',
            totalBytes,
            totalFiles: filePaths.length,
            elapsedMs: elapsed,
            avgSpeed: totalBytes / (elapsed / 1000),
        };
        this.emit('complete', result);
        this.emit('status', { state: this.state });
        return result;
    }

    /**
     * Send a single FileBlock over a specific channel.
     */
    _sendBlockToChannel(block, connection) {
        return new Promise((resolve, reject) => {
            try {
                const pathBuf = Buffer.from(block.path, 'utf8');
                // Header: type(2) + fileIndex(4) + pathLen(2) + path + lastModified(8)
                let headerSize = 2 + 4 + 2 + pathBuf.length + 8;
                if (block.isFile) {
                    // + totalSize(8) + blockIndex(4) + blockLength(4) + data
                    headerSize += 8 + 4 + 4;
                }

                const header = Buffer.alloc(headerSize);
                let offset = 0;

                header.writeUInt16BE(block.isFile ? TransferIdentifiers.FILE : TransferIdentifiers.FOLDER, offset);
                offset += 2;
                header.writeInt32BE(block.fileIndex, offset);
                offset += 4;
                header.writeUInt16BE(pathBuf.length, offset);
                offset += 2;
                pathBuf.copy(header, offset);
                offset += pathBuf.length;
                header.writeBigInt64BE(BigInt(Math.floor(block.lastModified)), offset);
                offset += 8;

                if (block.isFile) {
                    header.writeBigInt64BE(BigInt(block.totalSize), offset);
                    offset += 8;
                    header.writeInt32BE(block.blockIndex, offset);
                    offset += 4;
                    header.writeInt32BE(block.getLength(), offset);
                    offset += 4;
                }

                connection.socket.write(header);
                if (block.isFile && block.data) {
                    connection.socket.write(block.data);
                    connection.addUploadedBytes(block.getLength());
                }
                resolve();
            } catch (err) {
                reject(err);
            }
        });
    }

    async _sendBlock(block) {
        const conn = this.transferConnections[0];
        if (conn) await this._sendBlockToChannel(block, conn);
    }

    /**
     * Receive files from the connected device into destDir.
     * Listens on all transfer channels simultaneously.
     */
    async receiveFiles(destDir) {
        if (this.transferConnections.length === 0) {
            throw new Error('No transfer channels connected');
        }

        this.state = 'transferring';
        this.emit('status', { state: this.state, direction: 'download' });

        this.speedMonitor = new SpeedMonitor(this.transferConnections, (data) => {
            this.emit('speed', data);
        });
        this.speedMonitor.start();

        const startTime = Date.now();
        let totalBytes = 0;

        // Set up receive listeners on all channels
        const receivePromises = this.transferConnections.map((conn) => {
            return this._receiveFromChannel(conn, destDir, (bytes) => {
                totalBytes += bytes;
                this.emit('progress', { bytesReceived: totalBytes });
            });
        });

        await Promise.all(receivePromises);

        this.speedMonitor.stop();
        const elapsed = Date.now() - startTime;
        this.state = 'connected';

        const result = {
            direction: 'download',
            totalBytes,
            elapsedMs: elapsed,
            avgSpeed: totalBytes / (elapsed / 1000),
        };
        this.emit('complete', result);
        this.emit('status', { state: this.state });
        return result;
    }

    /**
     * Receive file blocks from a single channel.
     */
    _receiveFromChannel(connection, destDir, onBytes) {
        return new Promise((resolve, reject) => {
            let buffer = Buffer.alloc(0);
            const openFiles = new Map(); // fileIndex -> { fd, path }

            const processBuffer = () => {
                while (buffer.length >= 2) {
                    const type = buffer.readUInt16BE(0);

                    if (type === TransferIdentifiers.EOF ||
                        type === TransferIdentifiers.END_OF_INTERRUPTED ||
                        type === TransferIdentifiers.END_OF_READ_ERROR ||
                        type === TransferIdentifiers.END_OF_WRITE_ERROR) {
                        // Close all open files
                        for (const [, info] of openFiles) {
                            fs.closeSync(info.fd);
                        }
                        resolve();
                        return;
                    }

                    // Need at least: type(2) + fileIndex(4) + pathLen(2) = 8
                    if (buffer.length < 8) return;

                    const fileIndex = buffer.readInt32BE(2);
                    const pathLen = buffer.readUInt16BE(6);

                    if (buffer.length < 8 + pathLen + 8) return;

                    const filePath = buffer.slice(8, 8 + pathLen).toString('utf8');
                    const lastModified = Number(buffer.readBigInt64BE(8 + pathLen));
                    let headerEnd = 8 + pathLen + 8;

                    if (type === TransferIdentifiers.FOLDER) {
                        // Create directory
                        const fullPath = path.join(destDir, filePath);
                        fs.mkdirSync(fullPath, { recursive: true });
                        buffer = buffer.slice(headerEnd);
                        continue;
                    }

                    // FILE: need totalSize(8) + blockIndex(4) + blockLength(4)
                    if (buffer.length < headerEnd + 16) return;

                    const totalSize = Number(buffer.readBigInt64BE(headerEnd));
                    const blockIndex = buffer.readInt32BE(headerEnd + 8);
                    const blockLength = buffer.readInt32BE(headerEnd + 12);
                    headerEnd += 16;

                    if (buffer.length < headerEnd + blockLength) return;

                    const data = buffer.slice(headerEnd, headerEnd + blockLength);
                    buffer = buffer.slice(headerEnd + blockLength);

                    // Write to file
                    const fullPath = path.join(destDir, filePath);
                    const dir = path.dirname(fullPath);
                    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

                    if (!openFiles.has(fileIndex)) {
                        const fd = fs.openSync(fullPath, 'w');
                        openFiles.set(fileIndex, { fd, path: fullPath });
                    }

                    const fileInfo = openFiles.get(fileIndex);
                    const writeOffset = blockIndex * BLOCK_SIZE;
                    fs.writeSync(fileInfo.fd, data, 0, data.length, writeOffset);

                    connection.addDownloadedBytes(blockLength);
                    onBytes(blockLength);
                }
            };

            connection.socket.on('data', (chunk) => {
                buffer = Buffer.concat([buffer, chunk]);
                processBuffer();
            });

            connection.socket.on('error', (err) => {
                console.error(`Channel ${connection.name} error:`, err.message);
                reject(err);
            });

            connection.socket.on('close', () => {
                // If we haven't resolved yet, resolve now
                for (const [, info] of openFiles) {
                    try { fs.closeSync(info.fd); } catch (e) { }
                }
                resolve();
            });
        });
    }

    /**
     * Register a new transfer channel.
     */
    addTransferChannel(socket, name) {
        const conn = new TransferConnection(socket, name);
        this.transferConnections.push(conn);
        console.log(`✅ Transfer channel added: ${name} (${socket.remoteAddress})`);
        this.emit('channel', { name, address: socket.remoteAddress, total: this.transferConnections.length });
        return conn;
    }

    /**
     * List files in a local directory.
     */
    listLocalFiles(dirPath) {
        const resolvedPath = path.resolve(dirPath || this.homeDir);
        const entries = fs.readdirSync(resolvedPath, { withFileTypes: true });
        return entries.map(e => {
            const fullPath = path.join(resolvedPath, e.name);
            let stat;
            try { stat = fs.statSync(fullPath); } catch { stat = null; }
            return {
                name: e.name,
                path: fullPath,
                isFile: e.isFile(),
                isDirectory: e.isDirectory(),
                size: stat && e.isFile() ? stat.size : 0,
                lastModified: stat ? stat.mtimeMs : 0,
            };
        });
    }

    stop() {
        if (this.speedMonitor) this.speedMonitor.stop();
        this.transferConnections.forEach(c => c.destroy());
        this.transferConnections = [];
        if (this.controlSocket) this.controlSocket.destroy();
        if (this.controlServer) this.controlServer.close();
        this.state = 'idle';
        this.emit('status', { state: this.state });
    }
}

module.exports = { TransferEngine };
