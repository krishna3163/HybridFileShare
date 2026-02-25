# HybridLink - Complete Deployment Guide

## 🚀 Part 1: Vercel Web App Deployment

### Prerequisites
- GitHub account with repository
- Vercel account (free tier available)
- Node.js 18+ installed locally

### Step 1: Prepare Your Repository

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/HybridFileShare.git
cd HybridFileShare

# 2. Navigate to dashboard
cd dashboard

# 3. Install dependencies
npm install

# 4. Test locally
npm run dev
# Should run on http://localhost:5173
```

### Step 2: Deploy to Vercel

#### Option A: Via GitHub (Recommended - Auto-Deploy)

1. **Push to GitHub:**
```bash
cd HybridFileShare
git add .
git commit -m "Add web app and deployment configs"
git push origin main
```

2. **Connect to Vercel:**
   - Go to https://vercel.com/import
   - Click "Import Git Repository"
   - Select your HybridFileShare repo
   - Click "Import"

3. **Configure Build Settings:**
   - Framework: Vite
   - Root Directory: `./dashboard`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

4. **Environment Variables:**
   - Add `VITE_API_URL`: `https://api.hybridlink.share`
   - Add `VITE_APP_VERSION`: `0.1.0`

5. **Click "Deploy"**
   - Vercel will build and deploy automatically
   - You'll get a live URL like: `https://hybridlink.vercel.app`

#### Option B: Via Vercel CLI

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. From dashboard directory
cd dashboard

# 3. Deploy
vercel

# 4. Choose:
# - Set up and deploy? (y)
# - Which scope? (your-account)
# - Link to existing project? (n)
# - Project name? (hybridlink)
# - In which directory is your code? (./)

# 5. Done! You'll get a deployment URL
```

### Step 3: Configure Custom Domain (Optional)

1. **In Vercel Dashboard:**
   - Go to Project Settings
   - Click "Domains"
   - Add your domain
   - Follow DNS configuration

2. **DNS Setup:**
```
Type: CNAME
Name: www (or subdomain)
Value: cname.vercel.app
```

### Step 4: Set Up Auto-Deployment

**GitHub Actions will automatically:**
- Build on every push
- Run tests
- Deploy to Vercel

Configuration already in: `.github/workflows/deploy-web.yml`

---

## 🤖 Part 2: Android APK Automatic Build

### Setup GitHub Actions APK Build

The workflow is already configured in `.github/workflows/build-apk.yml`

**How it works:**
1. On every push to `main` → Builds debug APK
2. On pull requests → Builds debug APK (tests)
3. On git tags → Builds and releases both debug + release APK

### Release APK (for Play Store)

#### Step 1: Generate Upload Key

```bash
# Create signing key
keytool -genkey -v -keystore upload-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias hybridlink

# Save the password somewhere safe!
```

#### Step 2: Add Secrets to GitHub

Go to your GitHub repo → Settings → Secrets → New repository secret

Add these secrets:
- `KEYSTORE_BASE64`: Base64 of your upload-key.jks
- `KEYSTORE_PASSWORD`: Your keystore password
- `KEY_PASSWORD`: Your key password
- `KEY_ALIAS`: `hybridlink`

#### Step 3: Convert Keystore to Base64

```bash
# On Windows PowerShell
$keystore = [Convert]::ToBase64String((Get-Content -Path "upload-key.jks" -Encoding Byte))
$keystore | Set-Clipboard

# Then paste into GitHub Secret: KEYSTORE_BASE64
```

### Step 4: Upload to Play Store

1. Go to Google Play Console
2. Create new app "HybridLink"
3. In Release section → Create release
4. Upload APK from GitHub Releases

---

## 🌐 Part 3: Backend API Deployment

### Option A: Deploy to Vercel (Recommended)

```bash
# 1. Create api directory with structure
api/
├── package.json
├── server.js
├── vercel.json

# 2. package.json (api/)
{
  "name": "hybridlink-api",
  "version": "1.0.0",
  "scripts": {
    "start": "node server.js",
    "dev": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "multer": "^1.4.5",
    "bonjour": "^0.3.5",
    "uuid": "^9.0.0"
  }
}

# 3. Deploy
cd api
vercel

# 4. Get API URL: https://api.hybridlink.vercel.app
```

### Option B: Deploy to Railway / Render

**Railway.app:**
```bash
# 1. Connect GitHub repo
# 2. Select api/ directory
# 3. Automatic deployment
# 4. Get URL: https://hybridlink-api-production.up.railway.app
```

**Render.com:**
```bash
# 1. New Web Service
# 2. Connect GitHub repo
# 3. Build Command: npm install
# 4. Start Command: node server.js
# 5. Environment: NODE_ENV=production
```

### Option C: Docker + Any Cloud

```dockerfile
# Dockerfile (in api/ directory)
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

Deploy to:
- Google Cloud Run
- AWS ECS
- Azure Container Instances
- DigitalOcean App Platform

---

## 📱 Part 4: Windows App Packaging

### Create Windows Installer

```powershell
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build executable
pyinstaller --onefile `
  --windowed `
  --name "HybridLink" `
  --icon=icon.ico `
  windows-client/pc.py

# 3. Installer output in: dist/HybridLink.exe

# 4. Create installer with NSIS
# - Download NSIS: https://nsis.sourceforge.io
# - Create hybridlink-installer.nsi
# - Compile to get setup executable
```

**NSIS Installer Script Example:**
```nsis
!include "MUI2.nsh"

Name "HybridLink"
OutFile "HybridLink-Installer.exe"
InstallDir "$PROGRAMFILES\HybridLink"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\HybridLink.exe"
  
  CreateShortcut "$SMPROGRAMS\HybridLink.lnk" "$INSTDIR\HybridLink.exe"
  CreateShortcut "$DESKTOP\HybridLink.lnk" "$INSTDIR\HybridLink.exe"
SectionEnd
```

---

## 🔄 Part 5: Complete Deployment Workflow

### Development → Production Pipeline

```
┌─────────────────────┐
│   Local Development │
│  (npm run dev)      │
└──────────┬──────────┘
           │ git push
           ▼
┌──────────────────────┐
│   GitHub Repository  │
│  (main branch)       │
└──────────┬───────────┘
           │
      ┌────┴────┬────────┬──────────┐
      │          │        │          │
      ▼          ▼        ▼          ▼
  ┌──────┐  ┌─────┐  ┌──────┐  ┌────────┐
  │ Web  │  │ APK │  │ API  │  │Windows │
  │Vercel│  │CI/CD│  │Deploy│  │Publish │
  └──────┘  └─────┘  └──────┘  └────────┘
      │          │        │          │
      ▼          ▼        ▼          ▼
   Live    Releases   Production  Installer
   URL     Page       API         Available
```

---

## 📊 Deployment Checklist

### Before Going Live

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Environment variables set
- [ ] Database migrations done
- [ ] Security headers configured
- [ ] SSL certificates valid
- [ ] Rate limiting enabled
- [ ] Error logging configured
- [ ] CDN cache rules set
- [ ] Backups configured

### Verification Steps

```bash
# 1. Test Web App
curl https://hybridlink.vercel.app/health

# 2. Test API
curl https://api.hybridlink.vercel.app/health

# 3. Test File Transfer
curl -X POST https://api.hybridlink.vercel.app/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"deviceName":"test","type":"web"}'

# 4. Download APK
# - Go to GitHub Releases
# - Install hybridlink-release.apk

# 5. Test QR Code Generation
# - Open web app
# - Click "Share Files"
# - Verify QR code displays
```

---

## 🔐 Security Configuration

### Environment Variables

**Web App (.env):**
```
VITE_API_URL=https://api.hybridlink.vercel.app
VITE_MAX_FILE_SIZE=10GB
```

**API Server (.env):**
```
NODE_ENV=production
PORT=3000
CORS_ORIGIN=https://hybridlink.vercel.app
JWT_SECRET=your-secret-key-here
```

### Enable CORS Securely

```javascript
// In server.js
const corsOptions = {
  origin: process.env.CORS_ORIGIN || 'https://hybridlink.vercel.app',
  credentials: true,
  optionsSuccessStatus: 200,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
};

app.use(cors(corsOptions));
```

### Rate Limiting

```javascript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // 100 requests per windowMs
});

app.use('/api/', limiter);
```

---

## 📈 Monitoring & Analytics

### Vercel Analytics
- Dashboard: https://vercel.com/dashboard
- Web Analytics included
- Performance metrics
- Error tracking

### Sentry Error Tracking

```javascript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  environment: process.env.NODE_ENV,
});
```

### Custom Monitoring

```bash
# Check deployment status
curl https://hybridlink.vercel.app/status

# View logs
vercel logs hybridlink

# Analytics
vercel analytics view
```

---

## 🆘 Troubleshooting

### Vercel Deployment Issues

**Problem: Build fails with "Cannot find module"**
```bash
# Solution: Clear cache and rebuild
vercel rebuild

# Or delete and redeploy
vercel remove hybridlink
vercel --prod
```

**Problem: Environment variables not working**
```bash
# Check in Vercel Dashboard:
# Settings → Environment Variables
# Redeploy after changing
vercel --prod
```

**Problem: API CORS errors**
```bash
# Add to API server:
app.use(cors({
  origin: 'https://hybridlink.vercel.app'
}));
```

### GitHub Actions Issues

**Problem: APK build fails**
```bash
# Check logs:
# GitHub → Actions → build-apk workflow → See logs

# Common fixes:
# - Update Gradle
# - Check Java version (use 11)
# - Verify AndroidManifest.xml syntax
```

### Local Testing

```bash
# Test web locally
cd dashboard && npm run dev

# Test API locally
cd api && npm run dev

# Test Android locally
cd app && ./gradlew run
```

---

## 📚 Documentation URLs

- **Vercel Docs:** https://vercel.com/docs
- **GitHub Actions:** https://docs.github.com/en/actions
- **Android Build:** https://developer.android.com/build
- **Express.js:** https://expressjs.com
- **Vite:** https://vitejs.dev

---

## 🎯 Next Steps

1. Deploy web app to Vercel (5 min)
2. Set up GitHub Actions APK build (2 min)
3. Deploy API server (5 min)
4. Test end-to-end transfers
5. Set up custom domain
6. Configure monitoring
7. Submit to Play Store

**Estimated total time: 30-60 minutes**

---

**Your HybridLink app is now ready for production!** 🎉
