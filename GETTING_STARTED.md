# 🎯 HybridLink - Getting Started (Step-by-Step)

This guide walks you through exactly what to do, step by step, with each command to run.

**Time needed**: 30 minutes total  
**Prerequisites**: Node.js 18+, npm, Git, code editor

---

## Step 1: Verify Prerequisites (2 minutes)

### Check Node.js and npm

```bash
# Open terminal/PowerShell

node --version
# Should show: v18.x.x or higher

npm --version
# Should show: 9.x.x or higher
```

**If not installed:**
- Download from: https://nodejs.org (LTS version)
- Install like normal software
- Restart terminal after install
- Run commands above again

---

## Step 2: Navigate to Project (1 minute)

```bash
# Go to project directory
cd HybridFileShare

# Verify you're in correct folder
ls  # macOS/Linux
dir  # Windows

# Should see: api/, dashboard/, .github/, etc.
```

---

## Step 3: Install & Start Backend API (5 minutes)

### Terminal #1 - Backend Server

```bash
# Go to API folder
cd api

# Install dependencies (first time only)
npm install
# This downloads all packages (might take 2-3 minutes)

# Start the server
npm run dev
# You should see:
# 🚀 HybridLink API Server running!
# ✅ HTTP:  http://localhost:3000
# ✅ WS:    ws://localhost:3000/ws
```

**Keep this terminal open!** You'll need it running.

---

## Step 4: Install & Start Frontend (5 minutes)

### Terminal #2 - Web App

```bash
# Open new terminal/command prompt
# Make sure you're STILL in HybridFileShare folder

cd dashboard

# Install dependencies (first time only)
npm install
# This might take 1-2 minutes

# Start the web app
npm run dev
# You should see:
# VITE v4.x.x ready in xxx ms
# ➜  Local:   http://localhost:5173/
```

**Keep this terminal open!** The web app runs here.

---

## Step 5: Open Web App in Browser (2 minutes)

### Open the app

```bash
# In your web browser, go to:
http://localhost:5173

# You should see:
- HybridLink logo
- "Share Files" button
- Device discovery list
- No errors in red
```

**If you see errors**: Check **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## Step 6: Test Everything Works (3 minutes)

### Test in Browser

1. **Open Developer Console** (F12)
   - Look for any red error messages
   - Should see blue info messages only

2. **Test "Share Files" Mode**
   - Click "Share Files"
   - Should see device list below
   - Should see QR code on right

3. **Test "Receive Files" Mode**
   - Click "Receive Files"
   - Should see PIN display
   - Should see QR code

4. **Check Nearby Devices**
   - Should see device list
   - Status: "offline" is OK (no other devices)

---

## Step 7: Test API Directly (2 minutes)

### Terminal #3 - Test Commands

```bash
# Open NEW terminal (keep other 2 running)
# You can be anywhere, doesn't matter

# Test health check
curl http://localhost:3000/health
# Should return: {"status":"ok","timestamp":"...","uptime":...}

# Test nearby devices
curl http://localhost:3000/api/devices/nearby
# Should return: {"devices":[],"count":0,"timestamp":"..."}

# If both return JSON without errors: ✅ Everything works!
```

---

## Step 8: Run Tests (5 minutes)

### Test Full Transfer Flow

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for complete test suite.

Quick test:
```bash
# Register a test device
curl -X POST http://localhost:3000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "test-device",
    "deviceName": "My Laptop",
    "platform": "win32"
  }'

# Response should include device ID
# ✅ If this works, API is ready
```

---

## Step 9: Commit to Git (3 minutes)

```bash
# Terminal #1, #2, or #3 (doesn't matter, API will keep running)

# Initialize git if needed
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial HybridLink setup"

# Verify
git log
# Should show your commit with current date
```

---

## Step 10: Deploy to Vercel (10 minutes)

### Create GitHub Repository

```bash
# Go to https://github.com/new
# Create repository "HybridFileShare"
# Choose public or private
# Don't add README (we already have one)
# Click "Create repository"

# You'll see instructions like:
# git remote add origin https://github.com/YOUR_USERNAME/HybridFileShare.git
# git branch -M main
# git push -u origin main

# Run those commands:
git remote add origin https://github.com/YOUR_USERNAME/HybridFileShare.git
git branch -M main
git push -u origin main
```

### Deploy to Vercel

```bash
# Go to https://vercel.com/new
# Click "Import Git Repository"
# Follow the wizard:
# 1. Select your GitHub repo
# 2. Framework: Vite
# 3. Build command: npm run build
# 4. Root directory: ./dashboard
# 5. Click Deploy

# Wait 2-3 minutes for build...
# You'll get URL like: https://hybridlink-xyz.vercel.app
```

---

## Step 11: Verify Production Deployment (2 minutes)

```bash
# Test via browser
https://your-deployment-url.vercel.app

# Should load exactly like localhost:5173
# And work the same way

# Test API from production
curl https://your-deployment-url.vercel.app/api/status
```

---

## 🎉 You're Done! 

**What you have running:**

- ✅ **Local Development**
  - Web app: http://localhost:5173
  - API: http://localhost:3000
  - Can share files between devices on same WiFi

- ✅ **Production Deployment**
  - Web app: https://your-deployment-url.vercel.app
  - Auto-updates on every git push

- ✅ **GitHub Ready**
  - Code backed up safely
  - GitHub Actions ready for APK builds

---

## 📌 Keep These Terminals Running

| Terminal | What's Running | Command |
|----------|-----------------|---------|
| #1 | Backend API | `cd api && npm run dev` |
| #2 | Frontend app | `cd dashboard && npm run dev` |
| #3 | Any other task | Optional |

---

## 🔄 Next Steps

### Option A: Continue Development

```bash
# Edit code in dashboard/src/App.jsx or api/server.js
# Changes auto-reload (Vite hot reload)
# Test in browser
# Commit and push
# Vercel auto-deploys
```

### Option B: Set Up Android Builds

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) Part 2

```bash
# 1. Generate signing key
keytool -genkey -v -keystore release.keystore ...

# 2. Add GitHub Secrets
# GitHub Repo → Settings → Secrets

# 3. Push code
git push origin main

# 4. GitHub Actions auto-builds APK
# Download from: GitHub → Actions → build-apk
```

### Option C: Enable Additional Features

- Enable end-to-end encryption
- Set up monitoring/logging
- Configure rate limiting
- Add database persistence

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for help.

---

## ✅ Checklist: You Should See

After following steps above:

- [ ] Terminal #1 shows "🚀 API Server running"
- [ ] Terminal #2 shows "VITE ready"
- [ ] Browser shows web app at localhost:5173
- [ ] Developer console has no red errors
- [ ] `curl localhost:3000/health` returns OK
- [ ] Git repo created and pushed
- [ ] Vercel deployment shows live URL

---

## 🐛 Troubleshooting This Setup

### Port 3000 or 5173 in use?

```bash
# Terminal #1 - Kill process using port 3000
lsof -i :3000 | grep node
kill -9 <PID>

# Terminal #2 - Kill process using port 5173
lsof -i :5173 | grep node
kill -9 <PID>

# Then restart npm run dev
```

### npm install fails?

```bash
# Clear cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Can't connect to API from web app?

```bash
# Check API is running
curl http://localhost:3000/health
# Should return JSON

# Check web app is making requests
# F12 → Network tab
# Make a request
# Should see it listed

# Check CORS settings in api/server.js
# Should include http://localhost:5173
```

### Still having issues?

👉 See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📞 Need Help?

| Problem | Solution |
|---------|----------|
| Port already in use | Kill process: `lsof -i :PORT` |
| Module not found | Delete node_modules, reinstall: `npm install` |
| API won't start | Check logs in Terminal #1, see TROUBLESHOOTING.md |
| Web app won't load | Check logs in Terminal #2, open DevTools (F12) |
| Can't deploy to Vercel | Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) Part 1 |

---

## 🎓 Learn More

For deeper information:

- 🚀 **Deploy & Configure** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 🧪 **Test Everything** → [TESTING_GUIDE.md](TESTING_GUIDE.md)
- 🔧 **Fix Issues** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📖 **Full Overview** → [PROJECT_README.md](PROJECT_README.md)
- ⚡ **Quick Answers** → [QUICK_START.md](QUICK_START.md)

---

## 📊 What's Running Now

```
Your Local Machine:
├── http://localhost:3000         ← API (Terminal #1)
├── http://localhost:5173         ← Web app (Terminal #2)
├── Bonjour broadcast             ← Device discovery on port 9002
└── Local file uploads            ← Temporary staging

Your Vercel Account:
├── https://your-app.vercel.app   ← Web app (auto-deployed)
└── GitHub repo                   ← Backup code (auto-synced)
```

---

## 🎯 You're Now Ready!

✅ **Local development**: Working  
✅ **Web app deployed**: Live on Vercel  
✅ **GitHub Actions**: Ready for APK builds  
✅ **Documentation**: Complete and included  
✅ **Testing**: Full suite ready  
✅ **Production ready**: Day 1  

**Next**: Invite friends, share files, celebrate! 🎉

---

*Questions?* See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

*Ready to go deeper?* Check out full guides linked above.

---

**Happy coding!** 🚀
