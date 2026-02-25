# 🧪 HybridLink Testing Guide

## Quick Start - Test Locally (10 minutes)

### Prerequisites
```bash
cd HybridFileShare
npm install
```

### Terminal 1: Start Backend API

```bash
cd api
npm install
npm run dev

# Output:
# 🚀 HybridLink API Server running!
# ✅ HTTP:  http://localhost:3000
# ✅ WS:    ws://localhost:3000/ws
# ✅ mDNS:  Broadcasting...
```

### Terminal 2: Start Frontend

```bash
cd dashboard
npm install
npm run dev

# Output:
# VITE v4.x.x ready in xxx ms
# ➜  Local:   http://localhost:5173/
```

### Terminal 3: Test with curl

```bash
# Test API health
curl http://localhost:3000/health

# Get server status
curl http://localhost:3000/api/status

# Discover nearby devices
curl http://localhost:3000/api/devices/nearby

# Register a test device
curl -X POST http://localhost:3000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "test-device-1",
    "deviceName": "My Laptop",
    "platform": "win32"
  }'

# Test file upload
curl -X POST http://localhost:3000/api/transfer/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "senderId": "test-device-1",
    "receiverId": "test-device-2",
    "fileName": "sample.txt",
    "fileSize": 1024
  }'
```

---

## Feature Testing Checklist

### 1. Device Discovery

#### Test mDNS Broadcasting
```bash
# On first machine
curl http://localhost:3000/api/devices/nearby

# On second machine (same WiFi)
# Should see first machine in the list
```

**Expected Result:**
```json
{
  "devices": [
    {
      "id": "device-1",
      "name": "MacBook-Pro",
      "host": "192.168.1.100",
      "port": 9002,
      "platform": "darwin",
      "status": "online"
    }
  ]
}
```

#### Test Device Registration
```bash
# Register device
curl -X POST http://localhost:3000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "mobile-1",
    "deviceName": "iPhone 14",
    "platform": "ios"
  }'

# Verify registration
curl http://localhost:3000/api/devices/mobile-1
```

---

### 2. File Transfer

#### Initiate Transfer
```bash
TRANSFER_ID=$(curl -s -X POST http://localhost:3000/api/transfer/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "senderId": "laptop-1",
    "receiverId": "iphone-1",
    "fileName": "presentation.pdf",
    "fileSize": 5242880
  }' | jq -r '.sessionId')

echo "Transfer ID: $TRANSFER_ID"
```

#### Upload File
```bash
# Upload as chunks
curl -X POST "http://localhost:3000/api/transfer/upload/$TRANSFER_ID" \
  -F "chunk=@/path/to/large-file" \
  -F "chunkIndex=0" \
  -F "totalChunks=4"

# Expected: Shows progress percentage
```

#### Check Status
```bash
curl "http://localhost:3000/api/transfer/status/$TRANSFER_ID"
```

**Expected Response:**
```json
{
  "sessionId": "abc-123-def",
  "status": "uploading",
  "progress": 50,
  "uploadedBytes": 2621440,
  "totalBytes": 5242880,
  "fileName": "presentation.pdf",
  "chunksReceived": 2
}
```

#### Complete Transfer
```bash
curl -X POST "http://localhost:3000/api/transfer/complete/$TRANSFER_ID" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "message": "Transfer complete",
  "sessionId": "abc-123-def",
  "downloadPath": "/api/transfer/download/abc-123-def",
  "file": {
    "name": "presentation.pdf",
    "size": 5242880
  }
}
```

---

### 3. WebSocket Real-Time Communication

#### Connect to WebSocket
```bash
# Using websocat (install: cargo install websocat)
websocat ws://localhost:3000/ws

# Type messages as JSON:
{"type": "ping"}

# Expected response:
{"type": "pong", "timestamp": "2024-01-15T10:30:00.000Z"}
```

#### Test Broadcast
```json
{
  "type": "broadcast",
  "message": "Hello everyone!"
}
```

#### Test Transfer Notification
```json
{
  "type": "transfer_start",
  "senderId": "device-1",
  "fileName": "photo.jpg",
  "sessionId": "transfer-123"
}
```

---

### 4. Web UI Testing

#### Open Browser
```
http://localhost:5173
```

#### Test Send Mode
1. Click "Share Files"
2. Select files to share (drag & drop or click to browse)
3. Choose receiving device from list
4. Click "Send"
5. Watch progress bar
6. Verify QR code displays

#### Test Receive Mode
1. Click "Receive Files"
2. Enter PIN from sending device
3. Verify QR code displays
4. Click "Copy Link" to share
5. Verify device appears in nearby list

#### Test Device Discovery
1. Open app on two devices
2. Both should see each other in "Nearby Devices"
3. Click on device to select for transfer
4. Status shows "online" or "offline"

#### Test QR Code
1. Generate QR code
2. Open on another device
3. Should auto-fill device info
4. Should enable transfer

---

### 5. Security Testing

#### Test PIN Validation
```bash
# Valid PIN
curl -X POST http://localhost:3000/api/auth/verify-pin \
  -H "Content-Type: application/json" \
  -d '{"deviceId": "dev-1", "pin": "1234"}'

# Invalid PIN
curl -X POST http://localhost:3000/api/auth/verify-pin \
  -H "Content-Type: application/json" \
  -d '{"deviceId": "dev-1", "pin": "1"}'

# Expected: 401 error
```

#### Test CORS
```bash
# Cross-origin request should work
curl -i -X OPTIONS http://localhost:3000/api/devices/nearby \
  -H "Origin: http://example.com"

# Should have CORS headers:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
```

---

### 6. Performance Testing

#### Test Large File Upload
```bash
# Create 500MB test file
dd if=/dev/zero of=largefile.bin bs=1M count=500

# Upload
time curl -X POST "http://localhost:3000/api/transfer/upload/$TRANSFER_ID" \
  -F "chunk=@largefile.bin" \
  -F "chunkIndex=0" \
  -F "totalChunks=1" \
  -w "\nTime: %{time_total}s"
```

#### Test Multiple Concurrent Transfers
```bash
# Start 3 transfers simultaneously
for i in {1..3}; do
  curl -X POST http://localhost:3000/api/transfer/initiate \
    -H "Content-Type: application/json" \
    -d "{\"senderId\": \"device-1\", \"receiverId\": \"device-$i\", \"fileName\": \"file-$i.txt\", \"fileSize\": 1024}" &
done
wait

# Check each status
curl http://localhost:3000/api/status
```

#### Load Testing
```bash
# Install Apache Bench
# macOS: brew install httpd
# Ubuntu: sudo apt install apache2-utils

# Test endpoints
ab -n 1000 -c 10 http://localhost:3000/health
ab -n 500 -c 5 http://localhost:3000/api/devices/nearby
```

---

### 7. Integration Testing

#### Full Transfer Flow
```bash
#!/bin/bash

# 1. Register sender
SENDER=$(curl -s -X POST http://localhost:3000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"sender-1","deviceName":"Sender","platform":"web"}' \
  | jq -r '.device.id')

# 2. Register receiver
RECEIVER=$(curl -s -X POST http://localhost:3000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"receiver-1","deviceName":"Receiver","platform":"web"}' \
  | jq -r '.device.id')

# 3. Initiate transfer
TRANSFER=$(curl -s -X POST http://localhost:3000/api/transfer/initiate \
  -H "Content-Type: application/json" \
  -d "{\"senderId\":\"$SENDER\",\"receiverId\":\"$RECEIVER\",\"fileName\":\"test.txt\",\"fileSize\":1024}" \
  | jq -r '.sessionId')

# 4. Upload file
curl -X POST "http://localhost:3000/api/transfer/upload/$TRANSFER" \
  -F "chunk=@test.txt" -F "chunkIndex=0" -F "totalChunks=1"

# 5. Complete transfer
curl -X POST "http://localhost:3000/api/transfer/complete/$TRANSFER"

# 6. Verify
curl "http://localhost:3000/api/transfer/status/$TRANSFER"
```

---

## Debugging Tips

### Enable Debug Logging
```bash
# Add to api/server.js
DEBUG=* npm run dev
```

### Monitor Network Traffic
```bash
# macOS
nettop -p node

# Linux
ss -tanup | grep 3000

# Real-time logs
tail -f /var/log/hybridlink.log
```

### Test mDNS Directly
```bash
# macOS
dns-sd -B _hybridlink._tcp local.

# Linux
avahi-browse -a -d local

# Windows
# Use ZeroConfServiceBrowser or search "bonjour"
```

### Check Port Availability
```bash
# macOS/Linux
lsof -i :3000

# Windows PowerShell
Get-NetTCPConnection -LocalPort 3000
```

---

## Deployment Testing

### Test Vercel Deployment
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy API
cd api
vercel

# 3. Get production URL
# https://hybridlink-api-xyz.vercel.app

# 4. Test endpoints
curl https://hybridlink-api-xyz.vercel.app/health
curl https://hybridlink-api-xyz.vercel.app/api/status
```

### Test Production Site
```bash
# Web app
https://hybridlink.vercel.app

# API
https://api.hybridlink.vercel.app/health

# WebSocket
wss://api.hybridlink.vercel.app/ws
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Port 3000 already in use** | `lsof -i :3000 && kill -9 <PID>` or use `PORT=3001 npm run dev` |
| **CORS errors** | Check CORS settings in api/server.js, ensure origins are registered |
| **Devices not discovering** | Check firewall port 9002, ensure on same WiFi network |
| **File upload fails** | Check `/api/uploads` directory exists, verify disk space |
| **WebSocket won't connect** | Ensure WebSocket protocol supported, check proxy settings |
| **Large files timeout** | Increase Vercel timeout: set `maxDuration` in vercel.json |

---

## Next Steps

1. ✅ All local tests passing
2. Deploy API to Vercel
3. Deploy web app to Vercel
4. Configure custom domain
5. Test production environment
6. Submit to app stores (Play Store, App Store)

**Happy Testing!** 🚀
