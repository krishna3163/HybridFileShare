# ⚡ HybridLink Quick Reference

## 🚀 Start Here (Choose One)

### Option 1: Local Development (5 min)
```bash
# Terminal 1
cd api && npm install && npm run dev

# Terminal 2  
cd dashboard && npm install && npm run dev

# Terminal 3 (optional)
curl http://localhost:3000/health
```

### Option 2: Deploy to Vercel (3 min)
```bash
# Just push to GitHub
git push origin main

# Vercel auto-deploys from:
# https://vercel.com/YOUR_USERNAME/HybridFileShare
```

### Option 3: Build Android APK (30 min)
```bash
# Automatic on every git push
# Download from: GitHub → Actions → build-apk → Artifacts

# Or manually:
cd android-app && ./gradlew build
```

---

## 📱 URLs After Startup

| Component | URL | Status |
|-----------|-----|--------|
| Web App | http://localhost:5173 | ✅ Dev |
| API Server | http://localhost:3000 | ✅ Dev |
| API Health | http://localhost:3000/health | ✅ Dev |
| WebSocket | ws://localhost:3000/ws | ✅ Dev |

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | ⭐ **Start here** - Complete setup |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | 🧪 How to test everything |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 🔧 Fix common issues |
| [PROJECT_README.md](PROJECT_README.md) | 📖 Full project overview |

---

## 🔗 API Endpoints

### Devices
```bash
# List nearby
curl http://localhost:3000/api/devices/nearby

# Register device
curl -X POST http://localhost:3000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"dev1","deviceName":"My Device"}'

# Get device info
curl http://localhost:3000/api/devices/dev1
```

### File Transfer
```bash
# Start transfer
curl -X POST http://localhost:3000/api/transfer/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "senderId":"sender","receiverId":"receiver",
    "fileName":"file.txt","fileSize":1024
  }'

# Check status
curl http://localhost:3000/api/transfer/status/SESSION_ID

# Expected response:
{
  "sessionId": "abc-123",
  "status": "uploading",
  "progress": 50,
  "uploadedBytes": 512,
  "totalBytes": 1024
}
```

---

## 🗂️ Directory Structure

```
HybridFileShare/
├── api/                 ← Backend (Node.js)
│   ├── server.js       ← Main server
│   ├── services/
│   │   └── discovery.js ← mDNS device detection
│   ├── package.json
│   └── vercel.json
│
├── dashboard/          ← Frontend (React)
│   ├── src/
│   │   ├── App.jsx    ← Main component
│   │   └── App.css    ← Styling
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
│
├── .github/
│   └── workflows/
│       └── build-apk.yml  ← GitHub Actions CI/CD
│
└── 📚 Documentation files (below)
```

---

## 📋 Installation Checklist

- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm updated (`npm --version`)
- [ ] Cloned repository (`git clone ...`)
- [ ] API dependencies installed (`cd api && npm install`)
- [ ] Frontend dependencies installed (`cd dashboard && npm install`)
- [ ] Can run API locally (`npm run dev` in api/)
- [ ] Can run Frontend locally (`npm run dev` in dashboard/)
- [ ] Health check passes (`curl http://localhost:3000/health`)

---

## 🧪 Quick Test

```bash
# Terminal 1: Start API
cd api && npm run dev

# Terminal 2: Start Frontend
cd dashboard && npm run dev

# Browser: Open
http://localhost:5173

# Chrome DevTools
F12 → Console

# Should see no errors, green checkmarks on all tests
```

---

## 🚢 Deployment Checklist

- [ ] All tests passing locally
- [ ] Code committed to git
- [ ] GitHub repo created and configured
- [ ] GitHub Secrets set up (if using APK):
  - [ ] ANDROID_KEYSTORE_BASE64
  - [ ] KEYSTORE_PASSWORD
- [ ] Vercel account created
- [ ] Repo imported to Vercel
- [ ] Build settings configured (Root: `dashboard`, Build: `npm run build`)
- [ ] Environment variables set
- [ ] First deploy successful
- [ ] Can access at vercel.app domain

---

## 🔐 Security Essentials

### Never commit:
```
❌ .env files
❌ Private keys
❌ Passwords
❌ API keys
✅ Use GitHub Secrets instead
```

### Always use:
```
✅ HTTPS in production
✅ Environment variables for secrets
✅ CORS restrictions
✅ Rate limiting
✅ Input validation
```

---

## 🐛 Quick Debugging

### API won't start?
```bash
# Check if port 3000 is free
lsof -i :3000

# Or use different port
PORT=3001 npm run dev
```

### Frontend won't load?
```bash
# Clear Vite cache
rm -rf .vite dist node_modules/.vite

# Reinstall
npm install

# Start fresh
npm run dev
```

### Devices not found?
```bash
# Check mDNS broadcast
curl http://localhost:3000/api/devices/nearby

# Check firewall allows port 9002
# Check both devices on same WiFi
```

### File upload fails?
```bash
# Check uploads directory exists
mkdir -p api/uploads

# Check disk space
df -h

# Check file size limit
# Default: 10GB (can increase in multer config)
```

---

## 📞 Help Resources

```bash
# See logs
npm run dev  # Shows all output

# More debugging
DEBUG=* npm run dev

# Check specific port
lsof -i :PORT_NUMBER

# Test API directly
curl -v http://localhost:3000/health

# Open browser console
F12 → Console → check for errors
```

---

## 🎯 Common Tasks

### Add new device type
```bash
# 1. Create device in app
# 2. Register in API
curl -X POST http://localhost:3000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"new-dev","deviceName":"New Device"}'

# 3. Verify in devices list
curl http://localhost:3000/api/devices
```

### Debug file transfer
```bash
# 1. Get all active transfers
curl http://localhost:3000/api/status

# 2. Check specific transfer
curl http://localhost:3000/api/transfer/status/SESSION_ID

# 3. Server logs show progress
# Watch Terminal 1 (API server) for real-time updates
```

### Enable dark mode
```bash
# Toggle in web app - check App.css
# Look for dark-mode class in CSS
```

---

## 🔄 Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ... edit files ...

# Commit
git add .
git commit -m "feat: add my feature"

# Push
git push origin feature/my-feature

# GitHub Actions automatically:
# 1. Builds APK
# 2. Runs tests
# 3. Creates artifact

# Create Pull Request on GitHub
```

---

## 🌐 Environment Variables

**Web App** (`.env` or in Vercel Dashboard)
```
VITE_API_URL=http://localhost:3000
VITE_WS_URL=ws://localhost:3000
```

**API Server** (`.env` file)
```
PORT=3000
NODE_ENV=development
CORS_ORIGIN=http://localhost:5173
```

---

## 📊 Performance Tips

| Action | Impact | Effort |
|--------|--------|--------|
| Enable caching | ⚡⚡⚡ | Low |
| Optimize images | ⚡⚡ | Medium |
| Chunk large files | ⚡⚡⚡ | Medium |
| Use CDN | ⚡⚡ | High |
| Database indexing | ⚡⚡⚡ | Medium |

---

## 🎓 Learning Resources

- Node.js: https://nodejs.org/docs
- React: https://react.dev
- Express: https://expressjs.com
- Vite: https://vitejs.dev
- WebSocket: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

---

## 🚨 Emergency Commands

```bash
# Kill stuck process
killall node

# Clear all caches
npm cache clean --force && rm -rf node_modules

# Force reinstall
rm -rf node_modules package-lock.json && npm install

# Check everything
npm doctor
node --version
npm --version
```

---

## ✅ Success Indicators

You're good to go when:

- ✅ `curl http://localhost:3000/health` returns `{"status":"ok"}`
- ✅ Web app loads at http://localhost:5173 without errors
- ✅ Can see "Nearby Devices" in the app
- ✅ Browser console has no red errors
- ✅ API server logs show incoming requests

---

**Need more help?** 
- 📖 Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 🧪 Check [TESTING_GUIDE.md](TESTING_GUIDE.md)  
- 🔧 See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

*Last updated: January 2024*
