# Getting Started with HybridLink-Core

Step-by-step guides to get HybridLink-Core up and running on your system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [First Transfer (USB)](#first-transfer-usb)
4. [First Transfer (WiFi)](#first-transfer-wifi)
5. [First Transfer (Dual)](#first-transfer-dual)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **Disk Space**: ~500 MB (for source code and dependencies)
- **Network**: 
  - USB cable (for ADB) - OR
  - WiFi network (both devices on same network)

### Check Python Version

```bash
python --version
# or
python3 --version
```

If you get "command not found", install Python 3.8+ from https://www.python.org/

### Install ADB (for USB transfers)

**Windows:**
```powershell
# Using Chocolatey
choco install adb

# Or download Android SDK Platform Tools
# https://developer.android.com/studio/releases/platform-tools
```

**macOS:**
```bash
# Using Homebrew
brew install android-platform-tools

# Or install from Android Studio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install android-tools-adb
```

**Verify ADB installation:**
```bash
adb version
```

---

## Installation

### Step 1: Clone/Download the Project

```bash
# Navigate to project directory
cd HybridLink-Core
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install HybridLink-Core

```bash
# Install in development mode (recommended for testing)
pip install -e .

# Or install with dev tools
pip install -e ".[dev]"
```

### Step 4: Verify Installation

```bash
# Should print version and usage
hybridlink --help

# Should show system status
hybridlink status
```

✅ **Installation Complete!**

---

## First Transfer (USB)

### Step 1: Prepare Android Device

1. Connect Android device via USB
2. Enable USB Debugging:
   - Settings → Developer Options (enable if not visible)
   - Enable "USB Debugging"
   - Device will ask for permission: **Tap Allow**

### Step 2: Verify ADB Connection

```bash
# List connected devices
adb devices

# Output should show:
# List of attached devices
# emulator-5554    device
# 192.168.1.100:5555    (if WiFi is also connected)
```

### Step 3: Enable USB Forwarding

```bash
# Forward PC port 9000 to device port 9000
adb forward tcp:9000 tcp:9000

# Verify forwarding
adb forward --list

# Output should show:
# 192.168.1.100:5555 tcp:9000 tcp:9000
```

### Step 4: Create Test File

```bash
# Create a small test file (10 MB)
# Windows:
fsutil file createnew test.bin 10485760

# macOS/Linux:
dd if=/dev/zero of=test.bin bs=1M count=10
```

### Step 5: Send File via USB

```bash
# Use localhost since we have USB forwarding
hybridlink send test.bin --host 127.0.0.1 --no-wifi

# Output:
# HybridLink-Core v0.1.0
# Sending: test.bin
# Destination: 127.0.0.1
# File size: 10.00 MB
# 
# [████████░░░░░░░░░░░░░░░░] 40.0%
# Speed: 150.25 Mbps
# ETA: 0:00:15
```

### Troubleshooting USB Connection Issues

**Device not appearing in `adb devices`:**
```bash
# 1. Check drivers are installed (Windows)
# 2. Disconnect and reconnect USB

# 3. Restart ADB daemon
adb kill-server
adb devices
```

**Permission denied errors:**
```bash
# 1. On Android: Tap "Allow" when prompted
# 2. Try disconnecting and reconnecting
# 3. Check device isn't in file transfer mode
```

**Port already in use:**
```bash
# Kill existing ADB sessions
adb kill-server

# Re-forward
adb forward tcp:9000 tcp:9000
```

---

## First Transfer (WiFi)

### Step 1: Prepare for WiFi

1. Connect both PC and Android to same WiFi network
2. Get Android device's IP address:
   ```bash
   adb shell ip addr show wlan0
   ```
   Look for line like: `inet 192.168.1.100/24`
   IP address is `192.168.1.100`

### Step 2: Create Test File

```bash
# Create 10 MB test file
# Windows:
fsutil file createnew test.bin 10485760

# macOS/Linux:
dd if=/dev/zero of=test.bin bs=1M count=10
```

### Step 3: Send via WiFi

```bash
# Replace 192.168.1.100 with your device's actual IP
hybridlink send test.bin --host 192.168.1.100 --no-usb

# Output should show:
# Connecting to WiFi at 192.168.1.100:9001
# Sending: test.bin
# File size: 10.00 MB
# Progress: 0.0% connected...
```

### Troubleshooting WiFi Connection Issues

**Connection refused:**
```bash
# 1. Verify Android device at that IP
ping 192.168.1.100

# 2. Ensure device is listening on port 9001
adb shell netstat | grep 9001

# 3. Check firewall on PC
# Disable firewall temporarily for testing
```

**Slow transfer speeds:**
```bash
# 1. Move closer to router
# 2. Check for interference (microwave, other 2.4GHz devices)
# 3. Move to 5GHz band if available
# 4. Reduce chunk size for higher latency networks:
hybridlink send test.bin --host 192.168.1.100 --chunk-size 2097152
```

---

## First Transfer (Dual)

### Step 1: Prepare Both Connections

1. USB via ADB:
   ```bash
   adb forward tcp:9000 tcp:9000
   ```

2. WiFi:
   ```bash
   adb shell ip addr show wlan0  # Get IP
   ```

### Step 2: Create Test File

```bash
# Create 50 MB test file for better speed comparison
# Windows:
fsutil file createnew test.bin 52428800

# macOS/Linux:
dd if=/dev/zero of=test.bin bs=1M count=50
```

### Step 3: Send via Both Channels

```bash
# Replace IP with actual device IP
hybridlink send test.bin --host 192.168.1.100

# Output shows both channels working:
# HybridLink-Core v0.1.0
# Sending: test.bin
# Destination: 192.168.1.100
# File size: 50.00 MB
# 
# USB: 150.0 Mbps | WiFi: 200.0 Mbps
# [████████████████░░░░░░░░] 60.0%
# Speed: 350.25 Mbps (combined!)
# ETA: 0:00:05
```

### Tips for Optimal Dual Transfer

1. **Channel Balance**: Let the engine automatically balance
2. **WiFi Quality**: Ensure good WiFi signal
3. **USB Cable**: Use high-quality USB 3.0 cable if available
4. **File Size**: Larger files (>100 MB) show better speedup

### Expected Speed Improvements

```
USB Only:          100-150 Mbps
WiFi Only:         150-300 Mbps
USB + WiFi:        250-450 Mbps (1.6-2.5x improvement)
```

---

## Advanced Usage

### Receive Files

#### From USB

```bash
# Setup forwarding first
adb forward tcp:9000 tcp:9000

# Get file size from device (e.g., 100 MB = 104857600 bytes)
hybridlink receive received.bin --file-size 104857600 --no-wifi
```

#### From WiFi

```bash
# Get device IP
DEVICE_IP=$(adb shell ip addr show wlan0 | grep -E "inet [^:]+" -o | grep -E "[0-9.]+$")

# Receive file
hybridlink receive received.bin --file-size 104857600 --no-usb
```

#### From Both Channels

```bash
# Let it use both automatically
hybridlink receive received.bin --file-size 104857600
```

### Resumable Transfers

See `examples/example_resumable_transfer.py` for checkpoint support:

```bash
python examples/example_resumable_transfer.py
```

### Custom Configuration

```bash
# Send with custom chunk size (8 MB)
hybridlink send large_file.zip --host 192.168.1.100 --chunk-size 8388608

# Send without integrity verification (faster but less safe)
hybridlink send file.zip --host 192.168.1.100 --no-verify

# Send only over USB
hybridlink send file.zip --host 127.0.0.1 --no-wifi

# Send only over WiFi
hybridlink send file.zip --host 192.168.1.100 --no-usb
```

---

## Python API Usage

### Send File (Programmatic)

```python
import asyncio
from pathlib import Path
from hybridlink_core import TransferController, TransferConfig

async def main():
    config = TransferConfig(
        chunk_size=4 * 1024 * 1024,  # 4 MB
        usb_enabled=True,
        wifi_enabled=True,
    )
    
    controller = TransferController(config)
    
    # Initialize
    await controller.initialize_sender(
        file_path=Path("test.bin"),
        destination_host="192.168.1.100"
    )
    
    # Connect
    await controller.connect_channels()
    
    # Monitor progress
    def on_progress(update):
        print(f"Progress: {update.progress_percent:.1f}%")
    
    controller.set_progress_callback(on_progress)
    
    # Send
    result = await controller.run_transfer(controller.send())
    return result

if __name__ == "__main__":
    success = asyncio.run(main())
    print("✓ Success!" if success else "✗ Failed!")
```

### Receive File (Programmatic)

```python
import asyncio
from pathlib import Path
from hybridlink_core import TransferController, TransferConfig

async def main():
    config = TransferConfig()
    
    controller = TransferController(config)
    
    # Initialize
    await controller.initialize_receiver(
        destination_path=Path("received.bin"),
        file_size=10485760  # 10 MB
    )
    
    # Connect
    await controller.connect_channels()
    
    # Receive
    result = await controller.run_transfer(controller.receive())
    return result

asyncio.run(main())
```

---

## Monitoring & Debugging

### Enable Debug Logging

```bash
# Linux/macOS:
LOG_LEVEL=DEBUG hybridlink send test.bin --host 192.168.1.100

# Windows:
set LOG_LEVEL=DEBUG
hybridlink send test.bin --host 192.168.1.100
```

### Monitor Network Usage

**Windows:**
```powershell
# Open Resource Monitor (Ctrl+Shift+Esc) or:
resmon
# Look at Network tab
```

**macOS:**
```bash
# Real-time network usage
nettop
```

**Linux:**
```bash
# Monitor interface
watch -n 1 'cat /proc/net/dev'

# Or use nethogs to see per-process
sudo nethogs
```

### Check Port Availability

```bash
# Windows:
netstat -an | findstr 9000

# macOS/Linux:
netstat -an | grep 9000
```

---

## Next Steps

1. **Read [API Reference](API_REFERENCE.md)** for complete API documentation
2. **Explore [Architecture](ARCHITECTURE.md)** to understand system design
3. **Check [Examples](examples/)** for more code samples
4. **Review [Configuration](README.md#configuration)** for tuning

---

## Quick Reference

### Common Commands

```bash
# Installation
pip install -e .

# First send
adb forward tcp:9000 tcp:9000
hybridlink send file.zip --host 127.0.0.1 --no-wifi

# WiFi send
hybridlink send file.zip --host 192.168.1.100 --no-usb

# Dual send
hybridlink send file.zip --host 192.168.1.100

# Check status
hybridlink status

# Enable debug
LOG_LEVEL=DEBUG hybridlink send file.zip --host 192.168.1.100
```

### Common Issues

```
✗ Device not found
→ Run: adb devices
→ Enable USB Debugging on device

✗ Connection refused
→ Run: adb forward tcp:9000 tcp:9000
→ Connect device via USB

✗ Network unreachable
→ Verify IP: adb shell ip addr show wlan0
→ Check firewall
→ Ensure same WiFi network
```

---

## Getting Help

- **Command Help**: `hybridlink --help`
- **Documentation**: See `docs/` folder
- **Examples**: Check `examples/` folder
- **Issues**: GitHub Issues
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)

---

## Success Indicators ✅

You'll know everything is working when:

- ✅ `hybridlink status` shows no errors
- ✅ USB transfers show ~100-150 Mbps
- ✅ WiFi transfers show ~150-300 Mbps
- ✅ Dual transfers show ~250-450 Mbps combined
- ✅ Files receive correctly with verified hashes
- ✅ Progress updates appear in real-time
- ✅ Transfer completes without errors

**Happy transferring!** 🚀
