<p align="center">
  <img src="./logo.png" width="120" alt="HybridLink Logo">
</p>

# HybridLink: High-Speed Multipath File Transfer System

HybridLink is a production-ready, cross-platform file transfer ecosystem designed to maximize throughput by simultaneously utilizing **USB (ADB)** and **WiFi** channels.

## 🚀 The Ecosystem

HybridLink consists of three primary components working in harmony:

1.  **[HybridLink-Core](./HybridLink-Core)**: The high-performance Python engine that orchestrates multipath scheduling, chunk assembly, and integrity verification.
2.  **[Web Dashboard](./dashboard)**: A modern, real-time monitoring interface built with Vite and Vanilla JS, featuring glassmorphism design and live performance metrics.
3.  **[Android App](./app)**: A premium Jetpack Compose application for mobile-to-PC transfers with a unified cyberpunk-inspired UI.

---

## ✨ Features

- ⚡ **Multipath Aggregation**: Combine USB and WiFi bandwidth for ultra-fast transfers.
- 🎨 **Modern UI/UX**: Cyberpunk-inspired dark theme with glassmorphism and smooth animations.
- 📊 **Real-time Diagnostics**: Live throughput graphs, chunk completion maps, and connection health monitoring.
- ✅ **Data Integrity**: SHA-256 verification and resumable transfer support.
- 🔄 **Bidirectional**: Seamlessly send and receive files between PC and Android.

---

## 🖥️ Web Dashboard Preview

The dashboard provides a "Mission Control" experience for your transfers:
- **Global Progress**: High-visibility progress tracking with estimated time remaining.
- **Dual Speed Meters**: Independent monitoring for USB and WiFi transport speeds.
- **Chunk Map**: Visual representation of file data blocks as they are processed.
- **System Console**: Live logs directly from the transfer engine.

---

## 📱 Mobile App Preview

The Android application offers a premium, dark-themed experience:
- **One-Tap Actions**: Quick "Send" and "Receive" workflows.
- **Connection Badges**: Real-time status of active transport links.
- **Grounded Design**: Built with modern Jetpack Compose components and smooth transitions.

---

## 🛠️ Quick Start

### 1. Requirements
- Python 3.9+
- Android Device with USB Debugging enabled
- Node.js (for Dashboard)

### 2. Setup Core Engine
```bash
cd HybridLink-Core
pip install -r requirements.txt
```

### 3. Run Dashboard
```bash
cd dashboard
npm install
npm run dev
```

### 4. Build Android App
Open the `app` folder in Android Studio and build the project.

---

## 🗺️ Roadmap
- [ ] Rust implementation of the Core engine for zero-overhead performance.
- [ ] End-to-end encryption (AES-256).
- [ ] Multi-device concurrent transfers.
- [ ] Automatic network discovery (no IP entry required).

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.

Built with ❤️ by the HybridLink Team.