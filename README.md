<p align="center">
  <img src="./logo.png" width="140" alt="HybridFileShare Logo">
</p>

<h1 align="center">HybridFileShare | Multipath Mission Control</h1>

<p align="center">
  <img src="https://img.shields.io/github/v/release/krishna3163/HybridFileShare?style=for-the-badge&color=22d3ee" alt="Release">
  <img src="https://img.shields.io/github/downloads/krishna3163/HybridFileShare/total?style=for-the-badge&color=8b5cf6" alt="Downloads">
  <img src="https://komarev.com/ghpvc/?username=krishna3163-hybrid&color=ec4899&style=for-the-badge&label=PROFILE+VIEWS" alt="Profile Views" />
  <img src="https://img.shields.io/github/repo-size/krishna3163/HybridFileShare?style=for-the-badge&color=10b981" alt="Repo Size">
  <img src="https://img.shields.io/github/license/krishna3163/HybridFileShare?style=for-the-badge" alt="License">
</p>

HybridFileShare is a next-generation file transfer ecosystem designed to maximize throughput by simultaneously utilizing **USB (ADB/RNDIS)**, **WiFi Local Network**, and **WiFi Direct/Hotspot** channels. Say goodbye to the limits of normal single-channel file sharing apps!

[![HybridLink Video Demo](https://images.unsplash.com/photo-1618761714954-0b8cd0026356?auto=format&fit=crop&w=1200&h=400&q=80)](https://github.com/krishna3163/HybridFileShare)

---

## 📸 Interface Previews & Capabilities

### 1. The Web Dashboard & Native PC App
The Mission Control gives you a full command-center view of the file transfer ecosystem. It features a Cyberpunk/Glassmorphic UI that seamlessly syncs with your PC or Android nodes.
![Dashboard UI](https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1000&q=80) 

### 2. Live Multipath Transfer
When a file transfers, the dashboard displays live speed meters for both **WiFi** and **USB**, actively combining their bandwidth to create extreme throughput speeds.
![Multipath Speeds](https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1000&q=80) 

### 3. QR Code & PIN Pairing
Connecting your smartphone and PC is beautifully simple. Scan the dynamically generated QR Code from your Mobile App, or enter the 4-digit generated PIN sequence.
![QR Code Scan](https://images.unsplash.com/photo-1595079676339-1534801ad6cb?auto=format&fit=crop&w=1000&q=80) 

### 4. Zero-Config mDNS Discovery
If devices are on the same network, they automatically detect each other using advanced Bonjour/mDNS protocols. No need to look up IP addresses manually!
![Device Discovery](https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80) 

### 5. Mobile Android UI (Jetpack Compose)
The Android App uses `Material 3` to give you smooth 120Hz animations. You can toggle "Engine Broadcasting", "Web Share", and connect to PCs instantly using the embedded Camera.
![Android UI](https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=1000&q=80) 

---

## 🚀 Key Buttons & Functions Explained

### Dashboard / PC Client
- **`Scan QR Code` Button**: Opens the QR Modal in-tab. Displays your local LAN IP encrypted as a `hybridlink://` URI. You can also switch to the `Scan QR` tab to activate your laptop's webcam to scan external nodes.
- **`Enter PIN Code` Button**: Opens the Dual-Tab PIN Modal. Displays an auto-generated 4-digit code (e.g., `8421`) for another device to type in, OR lets you type in a PIN displayed on someone else's screen.
- **`Settings ⚙️`**: Configure "Dark Mode", "Notifications", and "Auto-Accept Transfers" directly.
- **`Nearby Devices Panel`**: Constantly listens via `_hybridfileshare._tcp` mDNS services to detect capabilities of smartphones or PCs within 50 meters. Click the "Connect" button next to any discovered device.

### Android Application
- **`Activate Engine` Toggle**: Starts the local NsdManager service, broadcasting your phone's unique `Android_ID`, Name, and active interfaces to the whole room.
- **`Web Share` Toggle**: Instantly hosts a localized HTTP Server allowing older devices (or iPhones) to download files from your Android via a normal web browser.
- **`Camera Scanner` Button**: Opens the native camera pipeline to snap QR codes displayed on the Mission Control PC dashboard.

---

## ⚙️ System Architecture & How it Works

HybridFileShare doesn't just use WiFi; it uses **Multipath Aggregation**.

```mermaid
graph TD
    subgraph "Android Device"
        A1[Android App UI] <--> A2[HybridLink Core Engine]
        A2 <--> A3((Local API / WebSocket))
        A2 <--> A4[mDNS Discovery Service]
    end

    subgraph "Desktop / Laptop"
        B1[Web / Tauri Dashboard] <--> B2[Node.js API Server]
        B2 <--> B3((Local API / WebSocket))
        B2 <--> B4[mDNS Bonjour Service]
    end

    subgraph "Network Links (Multipath)"
        C1[Wi-Fi Local Area Network]
        C2[USB Tethering / ADB Port Forwarding]
        C3[Wi-Fi Direct / Localhost]
    end

    A3 <-.->|Transfer 50% Data| C1
    A3 <-.->|Transfer 50% Data| C2
    A3 <-.->|Backup Data Link| C3
    B3 <-.->|Recv 50% Data| C1
    B3 <-.->|Recv 50% Data| C2
    B3 <-.->|Recv Backup Data| C3

    A4 <-.->|Presence Broadcast| C1
    B4 <-.->|Presence Scan| C1
```

1. **Discovery**: Both Node.js and Android broadcast themselves over UDP multicast via `mDNS`.
2. **Handshake**: A dual-channel WebSocket connects on Port 9001. A PIN/QR verifies identity.
3. **The Split**: When a 1GB file is sent, the core engine mathematically splits it. It routes 500MB over WiFi (`wlan0`) and simultaneously routes 500MB through a wired USB connection (`rndis0`).
4. **The Merge**: The receiving PC safely places all the asynchronous byte chunks back into a perfect 1GB file exactly securely verified by SHA-256 hashes.
5. **Telemetry**: A secondary WebSocket continuously blasts system metrics to the Web Dashboard to animate the speed meters 60 times a second.

---

## 🛠️ Installation & Setup

### For PC (Windows)
1. Go to [Releases](https://github.com/krishna3163/HybridFileShare/releases).
2. Download and run `HybridLink-Setup.exe`.
3. Open the app. It automatically handles the Node JS backend setup.

### For Android
1. Go to [Releases](https://github.com/krishna3163/HybridFileShare/releases).
2. Download `HybridFileShare.apk` and install it on your device.

*(For developers wanting to build from source, check the `dashboard` and `app` sub-directories).*

---

## 📊 Quick Tech Stack Summary
![Vite](https://img.shields.io/badge/vite-%23646CFF.svg?style=for-the-badge&logo=vite&logoColor=white) 
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![NodeJS](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white) 
![Tauri](https://img.shields.io/badge/tauri-%2324C8DB.svg?style=for-the-badge&logo=tauri&logoColor=%23FFFFFF) 
![Rust](https://img.shields.io/badge/rust-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white) 
![Android](https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white) 
![Kotlin](https://img.shields.io/badge/kotlin-%237F52FF.svg?style=for-the-badge&logo=kotlin&logoColor=white)


## 📄 License
MIT License - open source, free to reverse engineer, and modify!

Built with ❤️ by Krishna.