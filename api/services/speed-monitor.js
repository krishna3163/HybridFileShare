/**
 * SpeedMonitor — polls all TransferConnections every 1 second
 * and broadcasts per-channel speed data via a callback (usually WebSocket).
 */

class SpeedMonitor {
    /**
     * @param {TransferConnection[]} connections
     * @param {function} onSpeedUpdate - Called every second with speed data array
     */
    constructor(connections, onSpeedUpdate) {
        this.connections = connections;
        this.onSpeedUpdate = onSpeedUpdate;
        this.interval = null;
        this.running = false;
    }

    start() {
        if (this.running) return;
        this.running = true;
        this.interval = setInterval(() => {
            const data = this.connections.map(c => c.getAndResetTrafficDelta());
            const totalUploadSpeed = data.reduce((sum, d) => sum + d.uploadSpeed, 0);
            const totalDownloadSpeed = data.reduce((sum, d) => sum + d.downloadSpeed, 0);

            this.onSpeedUpdate({
                channels: data,
                totalUploadSpeed,
                totalDownloadSpeed,
                timestamp: Date.now(),
            });
        }, 1000);
    }

    stop() {
        this.running = false;
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

module.exports = { SpeedMonitor };
