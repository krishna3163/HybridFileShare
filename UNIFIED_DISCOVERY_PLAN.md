# Multitrack Unified Discovery Plan (2026)
### All Devices are Visible (APK, EXE, Web)

The "Multitrack Transfer" discovery system ensures that any device running the APK, EXE, or Web Dashboard on the same network is automatically visible and ready for multipath transfer.

## 1. Unified Protocol: mDNS (Bonjour/Zeroconf)
- **Service Name**: `_hybridfileshare._tcp.` (local network)
- **Role**: Every device acts as both an **Advertiser** (server) and a **Scanner** (client).
- **Metadata**: Each service includes a TXT record with:
  - `deviceId`: Unique persistent ID.
  - `deviceName`: User-friendly name (e.g., "Ashish's S24 Ultra").
  - `platform`: android, win32, or web.
  - `version`: Protocol version (1.0.0).

## 2. Implementation Matrix

| Component | Technology | Role | Status |
| :--- | :--- | :--- | :--- |
| **Android APK** | `NsdManager` (Kotlin) | Advertises `_hybridfileshare._tcp.` / Scans | ✅ Implemented |
| **Windows EXE** | `zeroconf` (Python Sidecar) | Advertises `_hybridfileshare._tcp.` / Scans | ✅ Implemented |
| **Web Dashboard** | `bonjour-service` (mDNS) | Advertises `_hybridfileshare._tcp.` / Scans | ✅ Implemented |

## 3. Visual Feedback (User Interface)
- **Radar Pulse**: Both Android and Windows clients display a radar-like scanning pulse in the "Nearby Devices" section.
- **Status Dots**:
  - 🔘 **Online**: Active heartbeat detected via mDNS.
  - 🔘 **Strong Connection**: Multipath (USB + WiFi) capability detected.
  - 🔘 **Stale**: Device was recently seen but heartbeat missed.
- **QR/PIN Fallback**: If mDNS is blocked by a router, QR scanning allows direct IP connection.

## 4. Cross-Platform Interaction
1. **EXE sees APK**: Windows client discovers the `_hybridfileshare` service from the phone and initiates a connection to the phone's IP:9001.
2. **APK sees EXE**: Android app discovers the PC's mDNS service and can initiate a send-request to the PC's IP:9001.
3. **Web sees All**: The local dashboard server (part of the API) populates the dashboard grid by scanning the local network in the background.

## 5. Security & Trust
- **PIN Verification**: Once a device is discovered, a one-time 4-digit PIN is used to establish a secure handshake.
- **Multitrack Bonding**: After the handshake, the engine bonds the WiFi channel with the USB ADB channel for maximum speed.

---
**Current Speed Benchmarks**:
- **USB 2.0 + WiFi 6**: ~150 MB/s (40 + 110 MB/s)
- **USB 2.0 + Dual WiFi (5G+2.4G)**: ~200+ MB/s
