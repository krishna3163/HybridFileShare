import os from 'os';
import { EventEmitter } from 'events';
import { Bonjour } from 'bonjour-service';

export class DeviceDiscovery extends EventEmitter {
  constructor(deviceId, deviceName = null) {
    super();

    this.deviceId = deviceId;
    this.deviceName = deviceName || `HybridFileShare-${os.hostname()}`;
    this.platform = process.platform;
    this.version = '1.0.0';
    this.port = 9002;
    this.serviceType = 'hybridfileshare';

    this.bonjour = new Bonjour();
    this.service = null;
    this.browser = null;
    this.discoveredDevices = new Map();

    // Heartbeats
    this.heartbeats = new Map();
  }

  /**
   * Start broadcasting this device on the local network
   */
  async startBroadcasting() {
    return new Promise((resolve) => {
      try {
        console.log(`✅ Advertising: ${this.deviceName} [${this.deviceId}]`);

        this.service = this.bonjour.publish({
          name: this.deviceName,
          type: this.serviceType,
          port: this.port,
          txt: {
            deviceId: this.deviceId,
            platform: this.platform,
            version: this.version
          }
        });

        this.service.on('up', () => {
          console.log(`🚀 Service is live: ${this.service.name}`);
        });

        this.emit('broadcasting', { deviceId: this.deviceId, name: this.deviceName });
        resolve();
      } catch (error) {
        console.error('❌ Failed to start broadcasting:', error);
        resolve();
      }
    });
  }

  /**
   * Start scanning for nearby devices
   */
  async startScanning() {
    return new Promise((resolve) => {
      try {
        console.log('🔍 Scanning for nearby multitrack devices...');

        this.browser = this.bonjour.find({ type: this.serviceType });

        this.browser.on('up', (service) => {
          const deviceId = service.txt?.deviceId || service.name;
          if (deviceId === this.deviceId) return;

          const host = service.addresses?.[0] || service.referer?.address || 'unknown';
          const device = {
            deviceId: deviceId,
            deviceName: service.txt?.deviceName || service.name,
            host: host,
            port: service.port,
            platform: service.txt?.platform || 'unknown',
            status: 'online',
            timestamp: Date.now()
          };

          this.discoveredDevices.set(deviceId, device);
          console.log(`✨ Device appeared: ${device.deviceName} (${device.host})`);
          this.emit('deviceAppeared', device);
        });

        this.browser.on('down', (service) => {
          const deviceId = service.txt?.deviceId || service.name;
          const device = this.discoveredDevices.get(deviceId);
          if (device) {
            device.status = 'offline';
            device.timestamp = Date.now();
            console.log(`👋 Device disappeared: ${device.deviceName}`);
            this.emit('deviceDisappeared', device);
          }
        });

        resolve();
      } catch (error) {
        console.error('❌ Failed to start scanning:', error);
        resolve();
      }
    });
  }

  getNearbyDevices() {
    return Array.from(this.discoveredDevices.values())
      .map(d => ({
        ...d,
        isStale: (Date.now() - d.timestamp) > 60000 // 60 sec stale
      }))
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  stop() {
    if (this.service) this.service.stop();
    if (this.browser) this.browser.stop();
    this.bonjour.destroy();
    console.log('🛑 Device discovery stopped');
    this.emit('stopped');
  }
}

// Singleton helper
let discoveryInstance = null;
export function getDiscoveryService(deviceId, deviceName) {
  if (!discoveryInstance) {
    discoveryInstance = new DeviceDiscovery(deviceId, deviceName);
  }
  return discoveryInstance;
}

export function closeDiscoveryService() {
  if (discoveryInstance) {
    discoveryInstance.stop();
    discoveryInstance = null;
  }
}

export default DeviceDiscovery;
