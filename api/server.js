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

app.get('/api/devices/nearby', (req, res) => {
  try {
    const nearbyDevices = Array.from(devices.values());
    
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

app.listen(port, () => {
  console.log(`\n🚀 HybridLink API Server running!`);
  console.log(`✅ HTTP:  http://localhost:${port}`);
  console.log(`✅ Health check: http://localhost:${port}/health`);
  console.log(`✅ Server ID: ${deviceId}\n`);
});

export default app;
