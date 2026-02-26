/**
 * TransferConnection — wraps a TCP socket for a single transfer channel.
 * Tracks upload/download byte counts for speed monitoring.
 */

class TransferConnection {
    /**
     * @param {net.Socket} socket - The raw TCP socket
     * @param {string} name - Human-friendly channel name (e.g. "WiFi", "USB_ADB")
     */
    constructor(socket, name) {
        this.socket = socket;
        this.name = name;
        this.uploadBytes = 0;
        this.downloadBytes = 0;
        this.lastUploadBytes = 0;
        this.lastDownloadBytes = 0;
        this.connected = true;
    }

    addUploadedBytes(n) {
        this.uploadBytes += n;
    }

    addDownloadedBytes(n) {
        this.downloadBytes += n;
    }

    /**
     * Returns traffic delta since last call, then resets counters.
     * Called by SpeedMonitor every 1 second.
     */
    getAndResetTrafficDelta() {
        const uploadDelta = this.uploadBytes - this.lastUploadBytes;
        const downloadDelta = this.downloadBytes - this.lastDownloadBytes;
        this.lastUploadBytes = this.uploadBytes;
        this.lastDownloadBytes = this.downloadBytes;
        return {
            name: this.name,
            uploadSpeed: uploadDelta, // bytes/sec
            downloadSpeed: downloadDelta,
            totalUploaded: this.uploadBytes,
            totalDownloaded: this.downloadBytes,
        };
    }

    resetTotalTraffic() {
        this.uploadBytes = 0;
        this.downloadBytes = 0;
        this.lastUploadBytes = 0;
        this.lastDownloadBytes = 0;
    }

    destroy() {
        this.connected = false;
        if (this.socket && !this.socket.destroyed) {
            this.socket.destroy();
        }
    }
}

module.exports = { TransferConnection };
