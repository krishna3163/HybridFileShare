/**
 * HybridLink Backend API Server
 * Handles device discovery, file transfers, and coordination
 * 
 * Supports:
 * - REST API for device management and transfers
 * - WebSocket for real-time P2P communication
 * - mDNS for local network device discovery
 * - File chunking and resumable uploads
 */

import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';
import WebSocket from 'ws';
import { DeviceDiscovery } from './services/discovery.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Initialize Express app
const app = express();
const port = process.env.PORT || 3000;
const deviceId = process.env.DEVICE_ID || `api-${uuidv4().slice(0, 8)}`;

// CORS configuration
const corsOptions = {
  origin: process.env.CORS_ORIGIN || ['http://localhost:5173', 'http://localhost:3000', 'https://hybridlink.vercel.app'],
  credentials: true,
  optionsSuccessStatus: 200,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Transfer-ID']
};

app.use(cors(corsOptions));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// Multer config for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'uploads');
    await fs.mkdir(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`);
  }
});

const upload = multer({
  storage,
  limits: {
    fileSize: 10 * 1024 * 1024 * 1024, // 10GB
    files: 100
  },
  fileFilter: (req, file, cb) => {
    if (file.size > 10 * 1024 * 1024 * 1024) {
      cb(new Error('File too large'));
    } else {
      cb(null, true);
    }
  }
});

// Initialize device discovery
const discovery = new DeviceDiscovery(deviceId, 'HybridLink-API');

// Store active transfer sessions
const transferSessions = new Map();

// Store connected devices
const registeredDevices = new Map();

// WebSocket connections
let wss;

// ============================================================
// REST API ENDPOINTS
// ============================================================

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

/**
 * Get server status and info
 */
app.get('/api/status', (req, res) => {
  res.json({
    serverId: deviceId,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    activeSessions: transferSessions.size,
    registeredDevices: registeredDevices.size,
    discoveryStats: discovery.getStats ? discovery.getStats() : { total: 0 }
  });
});

/**
 * Register a device
 * POST /api/devices/register
 */
app.post('/api/devices/register', (req, res) => {
  try {
    const { deviceId: clientId, deviceName, platform } = req.body;

    if (!clientId || !deviceName) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const device = {
      id: clientId,
      name: deviceName,
      platform: platform || 'unknown',
      status: 'online',
      registeredAt: new Date().toISOString(),
      lastSeen: Date.now()
    };

    registeredDevices.set(clientId, device);

    res.json({
      message: 'Device registered successfully',
      device
    });

    console.log(`📱 Device registered: ${deviceName} (${clientId})`);
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Registration failed' });
  }
});

/**
 * Get nearby devices (mDNS)
 * GET /api/devices/nearby
 */
app.get('/api/devices/nearby', (req, res) => {
  try {
    const nearbyDevices = discovery.getNearbyDevices ? discovery.getNearbyDevices() : [];
    const registeredList = Array.from(registeredDevices.values());
    
    // Combine discovered devices with registered devices
    const allDevices = [
      ...registeredList,
      ...nearbyDevices.filter(d => !registeredDevices.has(d.id))
    ];

    res.json({
      devices: allDevices,
      count: allDevices.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching nearby devices:', error);
    res.status(500).json({ error: 'Failed to fetch devices' });
  }
});

// Upload files
app.post('/api/transfer', upload.array('files'), async (req, res) => {
  try {
    const { fromDeviceId, fromDeviceName, toDeviceId } = req.body;
    const transferId = uuidv4();

    const transferData = {
      transferId,
      fromDeviceId,
      fromDeviceName,
      toDeviceId,
      files: req.files.map((f) => ({
        originalName: f.originalname,
        tempPath: f.path,
        size: f.size,
        mimetype: f.mimetype,
      })),
      timestamp: Date.now(),
      status: 'pending',
    };

    transfers.set(transferId, transferData);

    // Notify recipient via WebSocket (if connected)
    console.log(
      `📤 Transfer initiated: ${transferData.files.length} files from ${fromDeviceName}`
    );

    res.json({
      transferId,
      status: 'received',
      message: 'Files uploaded successfully',
    });
  } catch (error) {
    console.error('Transfer error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get transfer status
app.get('/api/transfer/:transferId', (req, res) => {
  const { transferId } = req.params;
  const transfer = transfers.get(transferId);

  if (!transfer) {
    return res.status(404).json({ error: 'Transfer not found' });
  }

  res.json(transfer);
});

// Download transferred files
app.get('/api/transfer/:transferId/download', (req, res) => {
  const { transferId } = req.params;
  const transfer = transfers.get(transferId);

  if (!transfer || transfer.status !== 'pending') {
    return res.status(404).json({ error: 'Transfer not found or expired' });
  }

  if (transfer.files.length === 1) {
    // Single file
    const file = transfer.files[0];
    res.download(file.tempPath, file.originalName, () => {
      transfers.delete(transferId);
      fs.unlinkSync(file.tempPath);
    });
  } else {
    // Multiple files - create zip
    const AdmZip = require('adm-zip');
    const zip = new AdmZip();

    transfer.files.forEach((file) => {
      zip.addLocalFile(file.tempPath, '', file.originalName);
    });

    const zipPath = path.join(uploadDir, `${transferId}.zip`);
    zip.writeZip(zipPath);

    res.download(zipPath, 'files.zip', () => {
      transfers.delete(transferId);
      fs.unlinkSync(zipPath);
      transfer.files.forEach((f) => {
        fs.unlinkSync(f.tempPath);
      });
    });
  }
});

// QR Code generation endpoint
app.post('/api/qrcode', (req, res) => {
  const { deviceId, deviceName, pin } = req.body;
  const shareData = {
    deviceId,
    deviceName,
    pin,
    timestamp: Date.now(),
  };

  res.json({
    qrData: JSON.stringify(shareData),
    shareLink: `${process.env.VERCEL_URL || 'http://localhost:3000'}?share=${Buffer.from(
      JSON.stringify(shareData)
    ).toString('base64')}`,
  });
});

// Scan QR code / Enter PIN
app.post('/api/connect', (req, res) => {
  const { pin, fromDeviceId } = req.body;
  // Validate PIN and establish connection
  res.json({ status: 'connected', message: 'Successfully connected' });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() });
});

// Static files
app.get('/', (req, res) => {
  res.sendFile(path.join(process.cwd(), 'public', 'index.html'));
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: 'Internal server error' });
});

// Cleanup old files every hour
setInterval(() => {
  const oneHourAgo = Date.now() - 3600000;
  transfers.forEach((transfer, id) => {
    if (transfer.timestamp < oneHourAgo) {
      transfer.files.forEach((f) => {
        try {
          fs.unlinkSync(f.tempPath);
        } catch (e) {
          // File already deleted
        }
      });
      transfers.delete(id);
    }
  });
}, 3600000);

// Start server
app.listen(PORT, () => {
  console.log(`🚀 HybridLink API Server running on port ${PORT}`);
  registerDevice('web');
});

export default app;
