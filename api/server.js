/**
 * HybridLink Backend API Server
 * Simple, working version for local development and production
 */

import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 3000;
const deviceId = `api-${uuidv4().slice(0, 8)}`;

// ============================================================
// MIDDLEWARE
// ============================================================

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

// Multer for file uploads
const upload = multer({
  dest: 'uploads/',
  limits: { fileSize: 10 * 1024 * 1024 * 1024 } // 10GB
});

// ============================================================
// IN-MEMORY STORAGE
// ============================================================

const devices = new Map();
const transferSessions = new Map();

// ============================================================
// HEALTH & STATUS
// ============================================================

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

app.get('/api/status', (req, res) => {
  res.json({
    serverId: deviceId,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    activeSessions: transferSessions.size,
    registeredDevices: devices.size
  });
});

// ============================================================
// DEVICE MANAGEMENT
// ============================================================

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

    devices.set(clientId, device);

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

// ============================================================
// DEVICE DISCOVERY (mDNS)
// ============================================================

import { getDiscoveryService } from './services/discovery.js';
const discovery = getDiscoveryService(deviceId, `HybridFileShare-${os.hostname()}`);

discovery.startBroadcasting().then(() => discovery.startScanning());

app.get('/api/local-ip', (req, res) => {
  const nets = os.networkInterfaces();
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      const familyV4Value = typeof net.family === 'string' ? 'IPv4' : 4;
      if (net.family === familyV4Value && !net.internal) {
        return res.json({ ip: net.address });
      }
    }
  }
  res.json({ ip: '127.0.0.1' });
});

app.get('/api/discover-devices', (req, res) => {
  try {
    const nearby = discovery.getNearbyDevices();
    res.json(nearby);
  } catch (error) {
    console.error('Discovery error:', error);
    res.status(500).json({ error: 'Failed to discover devices' });
  }
});

app.get('/api/devices/nearby', (req, res) => {
  try {
    const nearbyDevices = discovery.getNearbyDevices();
    res.json({
      devices: nearbyDevices,
      count: nearbyDevices.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching nearby devices:', error);
    res.status(500).json({ error: 'Failed to fetch devices' });
  }
});

app.get('/api/devices/:deviceId', (req, res) => {
  try {
    const device = devices.get(req.params.deviceId);

    if (!device) {
      return res.status(404).json({ error: 'Device not found' });
    }

    res.json(device);
  } catch (error) {
    console.error('Error fetching device:', error);
    res.status(500).json({ error: 'Failed to fetch device' });
  }
});

// ============================================================
// FILE TRANSFER
// ============================================================

app.post('/api/transfer/initiate', (req, res) => {
  try {
    const { senderId, receiverId, fileName, fileSize } = req.body;

    if (!senderId || !receiverId || !fileName) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const sessionId = uuidv4();
    const session = {
      id: sessionId,
      senderId,
      receiverId,
      fileName,
      fileSize,
      status: 'pending',
      createdAt: new Date().toISOString(),
      uploadedBytes: 0,
      chunks: new Map()
    };

    transferSessions.set(sessionId, session);

    console.log(`📤 Transfer initiated: ${sessionId} (${fileName})`);

    res.json({
      sessionId,
      message: 'Transfer session created',
      session
    });
  } catch (error) {
    console.error('Transfer initiation error:', error);
    res.status(500).json({ error: 'Failed to initiate transfer' });
  }
});

app.post('/api/transfer/upload/:sessionId', upload.single('chunk'), (req, res) => {
  try {
    const { sessionId } = req.params;
    const { chunkIndex, totalChunks } = req.body;

    const session = transferSessions.get(sessionId);
    if (!session) {
      return res.status(404).json({ error: 'Transfer session not found' });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    session.chunks.set(parseInt(chunkIndex), {
      path: req.file.path,
      size: req.file.size,
      uploadedAt: new Date()
    });

    session.uploadedBytes += req.file.size;
    session.status = 'uploading';

    const progress = Math.round((session.chunks.size / totalChunks) * 100);

    console.log(`📦 Chunk ${chunkIndex + 1}/${totalChunks} uploaded for ${sessionId} (${progress}%)`);

    res.json({
      chunkIndex,
      progress,
      uploadedBytes: session.uploadedBytes,
      message: progress === 100 ? 'Transfer complete' : 'Chunk received'
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
});

app.get('/api/transfer/status/:sessionId', (req, res) => {
  try {
    const session = transferSessions.get(req.params.sessionId);

    if (!session) {
      return res.status(404).json({ error: 'Transfer session not found' });
    }

    const progress = session.fileSize ? Math.round((session.uploadedBytes / session.fileSize) * 100) : 0;

    res.json({
      sessionId: session.id,
      status: session.status,
      progress,
      uploadedBytes: session.uploadedBytes,
      totalBytes: session.fileSize,
      fileName: session.fileName,
      chunksReceived: session.chunks.size
    });
  } catch (error) {
    console.error('Status check error:', error);
    res.status(500).json({ error: 'Failed to get transfer status' });
  }
});

app.post('/api/transfer/complete/:sessionId', (req, res) => {
  try {
    const session = transferSessions.get(req.params.sessionId);

    if (!session) {
      return res.status(404).json({ error: 'Transfer session not found' });
    }

    session.status = 'complete';
    session.completedAt = new Date();

    console.log(`✅ Transfer complete: ${req.params.sessionId} → ${session.fileName}`);

    res.json({
      message: 'Transfer complete',
      sessionId: session.id,
      downloadPath: `/api/transfer/download/${session.id}`,
      file: {
        name: session.fileName,
        size: session.fileSize
      }
    });
  } catch (error) {
    console.error('Completion error:', error);
    res.status(500).json({ error: 'Failed to complete transfer' });
  }
});

// ============================================================
// AUTH
// ============================================================

app.post('/api/auth/verify-pin', (req, res) => {
  try {
    const { deviceId, pin } = req.body;

    if (!deviceId || !pin) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Simple PIN verification
    const isValid = pin.length === 4 && /^\d+$/.test(pin);

    if (!isValid) {
      return res.status(401).json({ error: 'Invalid PIN' });
    }

    res.json({
      message: 'PIN verified',
      deviceId
    });
  } catch (error) {
    console.error('PIN verification error:', error);
    res.status(500).json({ error: 'Verification failed' });
  }
});

// ============================================================
// ============================================================
// TRANSFER ENGINE (Real File Transfer)
// ============================================================

import { createRequire } from 'module';
const require2 = createRequire(import.meta.url);
const { TransferEngine } = require2('./services/transfer-engine.js');

const transferEngine = new TransferEngine({
  controlPort: 5740,
  homeDir: os.homedir(),
});

// Start the transfer engine control server
transferEngine.startServer().then((port) => {
  console.log(`✅ Transfer Engine control channel on port ${port}`);
}).catch(err => {
  console.warn('⚠️ Transfer Engine could not start:', err.message);
});

// Forward transfer engine events to WebSocket telemetry
transferEngine.on('speed', (data) => {
  broadcastTelemetry('TRANSFER_SPEED', data);
});
transferEngine.on('progress', (data) => {
  broadcastTelemetry('TRANSFER_PROGRESS', data);
});
transferEngine.on('complete', (data) => {
  broadcastTelemetry('TRANSFER_COMPLETE', data);
});
transferEngine.on('status', (data) => {
  broadcastTelemetry('ENGINE_STATUS', data);
});
transferEngine.on('channel', (data) => {
  broadcastTelemetry('CHANNEL_CONNECTED', data);
});

// ============================================================
// FILE BROWSER API
// ============================================================

app.get('/api/list-files', (req, res) => {
  try {
    const dirPath = req.query.path || os.homedir();
    const files = transferEngine.listLocalFiles(dirPath);
    res.json({ path: dirPath, files });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/mkdir', (req, res) => {
  try {
    const { dirPath } = req.body;
    if (!dirPath) return res.status(400).json({ error: 'dirPath required' });
    const fs2 = require2('fs');
    fs2.mkdirSync(dirPath, { recursive: true });
    res.json({ success: true, path: dirPath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/delete', (req, res) => {
  try {
    const { filePath } = req.body;
    if (!filePath) return res.status(400).json({ error: 'filePath required' });
    const fs2 = require2('fs');
    const stat = fs2.statSync(filePath);
    if (stat.isDirectory()) {
      fs2.rmSync(filePath, { recursive: true, force: true });
    } else {
      fs2.unlinkSync(filePath);
    }
    res.json({ success: true, deleted: filePath });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/send', async (req, res) => {
  try {
    const { filePaths, remoteDir } = req.body;
    if (!filePaths || !Array.isArray(filePaths)) {
      return res.status(400).json({ error: 'filePaths array required' });
    }
    const result = await transferEngine.sendFiles(filePaths, remoteDir || '/sdcard/Download');
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/receive', async (req, res) => {
  try {
    const { destDir } = req.body;
    const dest = destDir || path.join(os.homedir(), 'Downloads', 'HybridFileShare');
    const fs2 = require2('fs');
    if (!fs2.existsSync(dest)) fs2.mkdirSync(dest, { recursive: true });
    const result = await transferEngine.receiveFiles(dest);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/transfer-status', (req, res) => {
  res.json({
    state: transferEngine.state,
    channels: transferEngine.transferConnections.length,
    progress: transferEngine.transferProgress,
  });
});

// ============================================================
// ERROR HANDLING
// ============================================================

app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ============================================================
// START SERVER
// ============================================================

// ============================================================
// START SERVER
// ============================================================

import { WebSocketServer } from 'ws';

// Create WebSocket server for telemetry on port 9002
const wss = new WebSocketServer({ port: 9002 });

wss.on('connection', (ws) => {
  console.log('📡 Dashboard/Client connected via WebSocket (Port 9002)');

  // Send a welcome message
  ws.send(JSON.stringify({
    type: 'SYSTEM_READY',
    data: {
      serverId: deviceId,
      version: '1.0.0'
    }
  }));

  ws.on('close', () => {
    console.log('👋 Dashboard/Client disconnected');
  });
});

// Helper to broadcast telemetry to all connected dashboards
export function broadcastTelemetry(type, data) {
  const payload = JSON.stringify({ type, data, timestamp: Date.now() });
  wss.clients.forEach((client) => {
    if (client.readyState === 1) { // 1 = OPEN
      client.send(payload);
    }
  });
}

const server = app.listen(port, () => {
  console.log(`\n🚀 HybridFileShare API Server running!`);
  console.log(`✅ HTTP:      http://localhost:${port}`);
  console.log(`✅ Telemetry: ws://localhost:9002`);
  console.log(`✅ Health:     http://localhost:${port}/health`);
  console.log(`✅ Server ID:  ${deviceId}\n`);
});

export default app;
