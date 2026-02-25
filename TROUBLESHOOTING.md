# 🔧 HybridLink Troubleshooting Guide

## Table of Contents
1. [Installation Issues](#installation)
2. [Development Server Issues](#dev-server)
3. [Deployment Issues](#deployment)
4. [Device Discovery Issues](#discovery)
5. [File Transfer Issues](#transfer)
6. [Security Issues](#security)
7. [Performance Issues](#performance)
8. [Getting Help](#help)

---

## <a name="installation"></a>🔨 Installation Issues

### Problem: NPM install fails

**Symptoms:**
```
npm ERR! code E404
npm ERR! 404 Not Found - GET https://registry.npmjs.org/package-name
```

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Or use specific registry
npm config set registry https://registry.npmjs.org/
npm install
```

---

### Problem: Node version incompatibility

**Symptoms:**
```
The engine "node" is incompatible with this package
```

**Solution:**
```bash
# Check current Node version
node --version

# Install Node 18+ using:
# macOS
brew install node@18

# Linux
curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows
# Download from https://nodejs.org (LTS version)

# Verify
node --version  # Should be v18.x.x or higher
```

---

### Problem: Port already in use

**Symptoms:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution:**
```bash
# macOS/Linux - Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use different port
PORT=3001 npm run dev

# Windows - Find process using port 3000
Get-NetTCPConnection -LocalPort 3000

# Kill process
Stop-Process -Id <PID> -Force

# Or use different port
set PORT=3001 && npm run dev
```

---

## <a name="dev-server"></a>🌐 Development Server Issues

### Problem: API server won't start

**Symptoms:**
```
Error: Cannot find module 'express'
```

**Solution:**
```bash
# Make sure you're in the correct directory
cd api

# Install dependencies
npm install

# Verify installation
npm list express

# Start server
npm run dev
```

---

### Problem: Frontend won't load

**Symptoms:**
```
VITE error: /src/App.jsx not found
```

**Solution:**
```bash
# Make sure you're in dashboard directory
cd dashboard

# Install dependencies
npm install

# Verify vite configuration
cat vite.config.js

# Clear vite cache
rm -rf .vite dist node_modules/.vite

# Start dev server
npm run dev
```

---

### Problem: WebSocket connection fails

**Symptoms:**
```
WebSocket is closed before the connection is established
```

**Solution:**
```bash
# Check if API server is running
curl http://localhost:3000/health

# Verify WebSocket URL in React app
# Should be: ws://localhost:3000/ws or wss:// for HTTPS

# Check browser console for errors
# Open DevTools → Console tab

# Verify CORS settings in server.js
# Should include your frontend origin

# Test WebSocket directly
npm install -g wscat
wscat -c ws://localhost:3000/ws
```

---

### Problem: File upload fails

**Symptoms:**
```
Error: File too large
413 Payload Too Large
```

**Solution:**
```bash
# Increase body limit in api/server.js
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));

# Increase multer limit
const upload = multer({
  limits: {
    fileSize: 10 * 1024 * 1024 * 1024 // 10GB
  }
});

# Restart API server
npm run dev
```

---

## <a name="deployment"></a>🚀 Deployment Issues

### Problem: Vercel build fails

**Symptoms:**
```
Build failed with 1 error:
error Command not found
```

**Solution:**
```bash
# Check vercel.json configuration
cat vercel.json

# Ensure correct build command
{
  "buildCommand": "cd dashboard && npm run build"
}

# Check package.json for build script
npm run build  # Test locally first

# Verify dist folder is created
ls -la dashboard/dist/

# Deploy with verbose output
vercel --prod --no-gitignore
```

---

### Problem: API deployment timeout

**Symptoms:**
```
504 Gateway Timeout
Function invocation timed out
```

**Solution:**
```bash
# Increase timeout in vercel.json
{
  "functions": {
    "server.js": {
      "maxDuration": 60  // Increase to 60 seconds
    }
  }
}

# Or deploy as standalone app
# Instead of Serverless function

# Check function logs
vercel logs api-production --follow
```

---

### Problem: Environment variables not working

**Symptoms:**
```
process.env.API_URL is undefined
```

**Solution:**
```bash
# 1. Set variables in Vercel Dashboard
# Settings → Environment Variables

# 2. Add for all environments:
# - Production
# - Preview
# - Development

# 3. Redeploy after changing
vercel --prod

# 4. Verify in browser
# Open DevTools → Network tab
# Check request headers for environment variable values

# 5. For React/Vite apps, prefix with VITE_
VITE_API_URL=https://api.example.com
```

---

### Problem: Domain not resolving

**Symptoms:**
```
Error: Cannot GET /
ERR_NAME_NOT_RESOLVED
```

**Solution:**
```bash
# Check DNS configuration
nslookup hybridlink.vercel.app

# Verify domain is connected in Vercel
# Settings → Domains

# Add DNS record (usually CNAME)
Type: CNAME
Name: www
Value: cname.vercel.app

# Test DNS propagation
dig hybridlink.vercel.app
host hybridlink.vercel.app
nslookup hybridlink.vercel.app

# Wait 24-48 hours for DNS propagation
```

---

## <a name="discovery"></a>📍 Device Discovery Issues

### Problem: Devices not found on local network

**Symptoms:**
```
GET /api/devices/nearby returns empty array
```

**Solution:**
```bash
# 1. Verify both devices are on same WiFi
ping other-device.local

# 2. Check mDNS is running
# Look for port 9002 listening
lsof -i :9002

# 3. Check firewall isn't blocking
# macOS
sudo spctl --status

# Windows Defender Firewall
netsh advfirewall firewall show rule name=all | grep 9002

# Linux iptables
sudo iptables -L -n | grep 9002

# 4. Manually add device IP
# Edit /etc/hosts or Windows hosts file
192.168.1.100 device-name.local

# 5. Test discovery endpoint
curl http://localhost:3000/api/devices/nearby

# 6. Check service broadcasting
curl 'http://localhost:3000/api/status'
# Should show devices in stats

# 7. Enable debug logging
DEBUG=bonjour npm run dev
```

---

### Problem: mDNS browser not finding devices

**Symptoms:**
```
bonjour.find() returns empty results
```

**Solution:**
```bash
# Check if mDNS service is properly published
# On service provider
console.log(discovery.getStats());

// On browser/client
const discovery = new DeviceDiscovery('device-1');
await discovery.startScanning();

// Listen for events
discovery.on('deviceUp', (device) => {
  console.log('Found:', device.name);
});

// Debug mDNS directly
# macOS
dns-sd -B _hybridlink._tcp local

# Linux
avahi-browse _hybridlink._tcp

# Windows
# Use Bonjour Browser app or online tools
```

---

### Problem: Offline devices showing as online

**Symptoms:**
```
Device status shows "online" but device is powered off
```

**Solution:**
```bash
# Reduce heartbeat interval
// In api/services/discovery.js
this.heartbeatInterval = 15000; // 15 seconds instead of 30

// Implement proper timeout detection
discovery.on('deviceTimeout', (device) => {
  console.log('Device timeout:', device.name);
  device.status = 'offline';
});

// Clear stale devices
setInterval(() => {
  discovery.clearStaleDevices(60000); // 1 minute
}, 30000);
```

---

## <a name="transfer"></a>📦 File Transfer Issues

### Problem: Transfer session expires

**Symptoms:**
```
404 Transfer session not found
```

**Solution:**
```bash
# Check transfer session timeout
// In api/server.js
const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours

// Clean up old sessions periodically
setInterval(() => {
  for (const [id, session] of transferSessions.entries()) {
    if (Date.now() - new Date(session.createdAt) > SESSION_TIMEOUT) {
      transferSessions.delete(id);
    }
  }
}, 60000);

# Increase upload timeout on frontend
const uploadTimeout = 300000; // 5 minutes
```

---

### Problem: Large file chunk fails mid-transfer

**Symptoms:**
```
Error: Connection reset by peer
Partial file uploaded
```

**Solution:**
```bash
# 1. Implement resumable uploads
// Store chunk checksums
const chunkHash = SHA256(chunkData);
session.chunks.set(chunkIndex, { hash: chunkHash, ... });

# 2. Add retry logic
const uploadChunks = async (file) => {
  for (let i = 0; i < chunks.length; i++) {
    let retries = 3;
    while (retries > 0) {
      try {
        await uploadChunk(chunks[i]);
        break;
      } catch (error) {
        retries--;
        if (retries === 0) throw error;
        await sleep(1000 * (4 - retries)); // Exponential backoff
      }
    }
  }
};

# 3. Reduce chunk size for unstable networks
CHUNK_SIZE = 1024 * 1024; // 1MB instead of 4MB
```

---

### Problem: Received file is corrupted

**Symptoms:**
```
Downloaded file is smaller than original
File won't open
```

**Solution:**
```bash
# 1. Add file integrity verification
import crypto from 'crypto';

const calculateHash = (data) => {
  return crypto.createHash('sha256').update(data).digest('hex');
};

// Verify before assembly
const sessionHash = calculateHash(completeFile);
if (sessionHash !== original.hash) {
  throw new Error('File integrity check failed');
}

# 2. Implement checksum validation
// Send checksum with each chunk
{
  chunkIndex: 0,
  chunkHash: sha256(data),
  totalChunks: 10
}

# 3. Verify at assembly time
for (let i = 0; i < totalChunks; i++) {
  const chunk = session.chunks.get(i);
  const data = await fs.readFile(chunk.path);
  if (calculateHash(data) !== chunk.hash) {
    throw new Error(`Chunk ${i} corrupted`);
  }
}
```

---

### Problem: Transfer speed is slow

**Symptoms:**
```
100MB file takes 10 minutes
```

**Solution:**
```bash
# 1. Increase chunk size
const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB

# 2. Increase concurrent uploads
const MAX_CONCURRENT_CHUNKS = 4;

const uploadConcurrent = async (chunks) => {
  for (let i = 0; i < chunks.length; i += MAX_CONCURRENT_CHUNKS) {
    const batch = chunks.slice(i, i + MAX_CONCURRENT_CHUNKS);
    await Promise.all(batch.map(uploadChunk));
  }
};

# 3. Check network connection
# macOS/Linux
iftop -i en0

# Windows
netsh interface tcp show global

# 4. Monitor server performance
# Check CPU and memory usage
top  # macOS/Linux
tasklist  # Windows

# 5. Use compression for text files
import zlib from 'zlib';

const gzip = (data) => zlib.gzipSync(data);
const gunzip = (data) => zlib.gunzipSync(data);
```

---

## <a name="security"></a>🔐 Security Issues

### Problem: PIN validation bypass

**Symptoms:**
```
Any 4-digit code works
```

**Solution:**
```bash
# Implement proper PIN validation
const isPinValid = (pin, stored) => {
  // Use constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(pin),
    Buffer.from(stored)
  );
};

# Add rate limiting
const pinAttempts = new Map();

app.post('/api/auth/verify-pin', (req, res) => {
  const attempts = pinAttempts.get(req.ip) || 0;
  
  if (attempts > 3) {
    return res.status(429).json({ error: 'Too many attempts' });
  }
  
  // ... verify PIN ...
});

# Implement PIN expiration
const PIN_LIFETIME = 5 * 60 * 1000; // 5 minutes
```

---

### Problem: CORS vulnerability

**Symptoms:**
```
Access-Control-Allow-Origin: *
```

**Solution:**
```bash
# 1. Restrict CORS to known origins
const corsOptions = {
  origin: ['https://hybridlink.vercel.app', 'http://localhost:3000'],
  credentials: true
};

app.use(cors(corsOptions));

# 2. Implement CSRF protection
const csrf = require('csurf');
app.use(csrf());

# 3. Set security headers
app.use((req, res, next) => {
  // Click-jacking protection
  res.set('X-Frame-Options', 'DENY');
  
  // MIME-type sniffing protection
  res.set('X-Content-Type-Options', 'nosniff');
  
  // XSS protection
  res.set('X-XSS-Protection', '1; mode=block');
  
  next();
});
```

---

### Problem: Exposed secrets

**Symptoms:**
```
API keys in source code
```

**Solution:**
```bash
# 1. Use environment variables
// Never commit secrets
require('dotenv').config();

const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error('API_KEY environment variable not set');
}

# 2. Configure GitHub secrets
# Go to: Settings → Secrets → New repository secret

# Add secret
Name: ANDROID_KEYSTORE_PASSWORD
Value: your-secret-password

# 3. Use in GitHub Actions
# .github/workflows/build.yml
env:
  KEYSTORE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}

# 4. Scan for secrets
npm install -g detect-secrets
detect-secrets scan
```

---

## <a name="performance"></a>⚡ Performance Issues

### Problem: React app is slow

**Symptoms:**
```
Page load time > 3 seconds
React rendering lag
```

**Solution:**
```bash
# 1. Analyze bundle size
npm run build
ls -lh dashboard/dist/

# 2. Enable code splitting
// React.lazy for route splitting
const Send = React.lazy(() => import('./Send'));
const Receive = React.lazy(() => import('./Receive'));

# 3. Optimize images
- Use WebP format
- Compress with imagemin
- Lazy load offscreen images

# 4. Use React DevTools Profiler
- Chrome DevTools → React tab → Profiler
- Record interactions
- Check for unnecessary re-renders

# 5. Implement React.memo for expensive components
const DeviceCard = React.memo(({ device, onClick }) => {
  return <div onClick={onClick}>{device.name}</div>;
});
```

---

### Problem: API endpoint is slow

**Symptoms:**
```
API response time > 1 second
Timeout errors
```

**Solution:**
```bash
# 1. Enable caching
import redis from 'redis';

const cache = redis.createClient();

app.get('/api/devices/nearby', async (req, res) => {
  const cached = await cache.get('nearby-devices');
  if (cached) return res.json(JSON.parse(cached));
  
  const devices = discovery.getNearbyDevices();
  await cache.setex('nearby-devices', 10, JSON.stringify(devices));
  res.json(devices);
});

# 2. Add database indexing
// For PostgreSQL
CREATE INDEX idx_device_id ON devices(device_id);
CREATE INDEX idx_transfer_status ON transfers(status);

# 3. Implement pagination
app.get('/api/devices/nearby?limit=10&offset=0');

# 4. Monitor performance
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path}: ${duration}ms`);
  });
  next();
});

# 5. Use APM tool
npm install elastic-apm-node
```

---

## <a name="help"></a>❓ Getting Help

### Where to find answers

| Resource | Link |
|----------|------|
| **GitHub Issues** | [Report bugs](https://github.com/YOUR_USERNAME/HybridFileShare/issues) |
| **GitHub Discussions** | [Ask questions](https://github.com/YOUR_USERNAME/HybridFileShare/discussions) |
| **Documentation** | [Read docs](./DEPLOYMENT_GUIDE.md) |
| **Testing Guide** | [Test locally](./TESTING_GUIDE.md) |

### How to report a bug

When reporting an issue, include:

1. **Reproduction steps:**
```
1. Open app
2. Click "Share Files"
3. Select device
4. Error occurs
```

2. **Expected behavior:**
```
Files should be transferred
```

3. **Actual behavior:**
```
Error: Transfer failed
```

4. **Environment:**
```
OS: Windows 11
Node: v18.x.x
Browser: Chrome 120
```

5. **Logs:**
```bash
# Paste error output from console
Error: ENOENT: no such file or directory
```

### Debug mode

Enable verbose logging:
```bash
# API
DEBUG=* npm run dev

# React
REACT_DEBUG=true npm run dev
```

---

## 📞 Still need help?

1. Search existing issues
2. Check [Testing Guide](./TESTING_GUIDE.md)
3. Create new GitHub issue with details above
4. Email: support@hybridlink.app

---

**Happy troubleshooting! 🔧**
