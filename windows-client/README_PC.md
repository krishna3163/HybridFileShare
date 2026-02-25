# Windows PC Implementation - HybridLink

**Dual-Channel Hybrid File Transfer Tool for Windows**

This is the Windows PC side of HybridLink - a powerful file transfer tool that uses **simultaneous USB (ADB) and WiFi channels** to accelerate transfers between Windows and Android devices.

## Features

✨ **Dual-Channel Transfer**
- USB channel via ADB port forwarding (wired, reliable, lower latency)
- WiFi channel via SSH/TCP (wireless, variable speed)
- Both channels work simultaneously for 2x+ throughput
- Automatic failover if one channel fails

🚀 **High Performance**
- Concurrent chunk processing on multiple channels
- Intelligent chunk scheduling based on live channel speed
- Configurable 512KB to 8MB chunks
- Scales from 100MB to 100GB+ files

📊 **Smart Scheduling**
- Real-time channel health monitoring
- Per-channel latency and error tracking
- Automatic assignment to fastest available channel
- Prevents slow channels from blocking transfers

✅ **Reliability**
- SHA256 file integrity verification
- Automatic retry for failed chunks
- Resume interrupted transfers seamlessly
- Atomic manifest checkpoints for crash safety

💻 **Windows First**
- Native Windows CMD/PowerShell compatibility
- Auto-detects ADB and connected devices
- No Linux-only dependencies
- Handles Windows file paths correctly

## Architecture

```
┌────────────────────────────────────────────┐
│         pc.py (Main CLI Tool)              │
│  Interactive & Command-line interface      │
└────────────────────┬───────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌─────────┐  ┌──────────┐  ┌─────────┐
   │ Windows │  │Manifest  │  │Dual-    │
   │ Utils   │  │Manager   │  │Channel  │
   │ (ADB)   │  │(Resume)  │  │Manager  │
   └────┬────┘  └──────┬───┘  └────┬────┘
        │              │           │
        └──────────────┼───────────┘
                       │
        ┌──────────────▼──────────────┐
        │   HybridLink-Core           │
        │   (Transfer Controller)     │
        ├─────────────────────────────┤
        │ • Chunk Management          │
        │ • Channel Management        │
        │ • Multi-Channel Scheduler   │
        │ • Progress Reporting        │
        │ • Integrity Verification    │
        └────┬─────────────────────┬──┘
             │                     │
        ┌────▼────┐            ┌──▼──────┐
        │  USB    │            │  WiFi   │
        │ (ADB)   │            │ (SSH)   │
        └────┬────┘            └──┬──────┘
             │                    │
         ┌───▼────────────────────▼────┐
         │   Android Device (Termux)   │
         │   phone.py (Receiver)       │
         └────────────────────────────┘
```

## Module Structure

### Core Modules (Windows-Specific)

| Module | Purpose |
|--------|---------|
| `pc.py` | Main CLI entry point for Windows users |
| `windows_utils.py` | ADB detection, device enumeration, Windows subprocess handling |
| `manifest_manager.py` | Persistent checkpoints for resume capability |
| `windows_connection_manager.py` | Dual-channel connection orchestration and health monitoring |

### Used from HybridLink-Core

| Module | Purpose |
|--------|---------|
| `transfer_controller.py` | Orchestrates send/receive operations |
| `chunk_manager.py` | File splitting and chunk tracking |
| `channel_manager.py` | Abstract transport layer |
| `multichannel_scheduler.py` | Intelligent chunk distribution across channels |
| `progress_reporter.py` | Real-time progress tracking |
| `integrity_verifier.py` | SHA256 verification |

## Installation

### Prerequisites

1. **Python 3.8+**
   ```powershell
   python --version
   ```

2. **Android SDK Platform Tools (ADB)**
   - Download: https://developer.android.com/tools/releases/platform-tools
   - Extract to: `C:\Android\sdk\platform-tools`
   - Verify: `adb --version`

3. **USB Drivers** (if needed)
   - Most modern Android devices work out of the box
   - On Windows, check Device Manager for proper driver

### Setup Steps

```powershell
# 1. Clone repository
git clone https://github.com/YOUR_REPO/HybridFileShare
cd HybridFileShare

# 2. Install dependencies
cd HybridLink-Core
pip install -r requirements.txt

# 3. Run pc.py (Windows client)
cd ../windows-client
python pc.py
```

## Usage

### Interactive Mode (Easiest)

```powershell
$ python pc.py
```

Follow the menu:
```
✓ HybridLink-Windows v0.1.0
✓ Dual-Channel Hybrid File Transfer Tool

🔍 Device Detection
ADB Version: Android Debug Bridge version 1.0.41

Connected Android Devices:
┏━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Serial       ┃ Name   ┃ Type   ┃ State   ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ FA6AW0A00143 │ Pixel  │📞 Phys │ device  │
└──────────────┴────────┴────────┴─────────┘

Main Menu
[1] Send file to Android
[2] Receive file from Android
[3] Configure device
[4] Exit

Select option (1-4): 1
File path to send: C:\Users\Admin\Downloads\backup.zip
Phone WiFi IP [192.168.1.100]: 
```

### Command Line Mode

**Send a file:**
```powershell
python pc.py send "C:\Data\large_file.zip" --phone 192.168.1.100
```

**Receive a file:**
```powershell
python pc.py receive "C:\Downloads\from_phone.bin" --file-size 536870912 --phone 192.168.1.100
```

### Advanced Options

```powershell
# Custom chunk size (1MB for slow networks)
python pc.py send myfile.iso --chunk-size 1048576 --phone 192.168.1.100

# USB only (no WiFi)
python pc.py send myfile.iso --no-wifi --phone 192.168.1.100

# Skip verification
python pc.py send myfile.iso --no-verify --phone 192.168.1.100
```

## Configuration

Configuration is stored in: `%APPDATA%\Local\HybridLink\pc_config.json`

Example:
```json
{
  "phone_ip": "192.168.1.100",
  "phone_ssh_port": 22,
  "usb_local_port": 9000,
  "chunk_size": 4194304,
  "verify_integrity": true
}
```

See `example_pc_config.json` for full options.

## Progress Display

During transfer, you'll see:

```
📤 Transferring
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ 44% ⏱ 0:02:15
↓ 22.5MB/s ↑ 11.2MB/s (USB: 12MB/s | WiFi: 10.5MB/s)
Chunks: 45/102
```

- Progress bar: Current transfer percentage
- Speed: Combined + per-channel speeds
- Chunks: Completed / Total chunks

## Features in Detail

### Dual-Channel Transfer

Transfer occurs simultaneously on both channels:

```
USB Channel (9000)     WiFi Channel (9001)
  │                        │
  ├─ Chunk 0           ├─ Chunk 1
  ├─ Chunk 2           ├─ Chunk 3
  ├─ Chunk 4           ├─ Chunk 5
  ├─ Chunk 6           ├─ Chunk 7
  └─ ...               └─ ...

Total Speed = USB speed + WiFi speed
```

### Intelligent Scheduling

The scheduler measures channel speeds and assigns chunks based on capacity:

```
┌─ Channel health checked every 2 seconds
├─ Speed measured via 1MB test transfer
├─ Quality score calculated: (availability) × (1 - latency_penalty)
└─ Chunks assigned to fastest available channel
```

### Resume Interrupted Transfers

Manifest file tracks completed chunks:

```
.hybridlink_SEND-20240115143022.manifest
├─ transfer_id: "SEND-20240115143022"
├─ file_size: 104857600
├─ chunk_size: 4194304
├─ total_chunks: 25
├─ completed_chunks: {0, 1, 2, 5, 7, ...}
└─ state: "transferring"
```

If interrupted, run the same command again - transfer resumes automatically.

## Troubleshooting

### ADB Not Found

```powershell
# Check if adb is in PATH
where adb

# If not, add to PATH
$env:PATH += ";C:\Android\sdk\platform-tools"

# Or specify explicitly in config
```

### No Devices Detected

```powershell
# 1. Connect phone via USB
# 2. Enable USB Debugging on phone (Settings > Developer Options)
# 3. Verify ADB sees it
adb devices -l

# 4. Grant USB permission on phone when prompted
# 5. Verify authorization
adb devices
```

### WiFi Connection Failed

```powershell
# 1. Get phone IP from ADB
adb shell ip addr show

# 2. Test SSH connectivity
ssh -p 22 user@192.168.1.100

# 3. Verify SSH running on phone
adb shell ps | findstr sshd

# 4. Check firewall allows port 9001
```

### Slow Transfer Speed

```powershell
# 1. Check both channels active
python pc.py send file.iso --phone 192.168.1.100
# Should see both USB and WiFi speeds

# 2. Reduce chunk size for unreliable networks
python pc.py send file.iso --chunk-size 1048576 --phone 192.168.1.100

# 3. Use USB only if WiFi problematic
# (Set wifi_enabled: false in config)

# 4. Improve WiFi signal
```

## Performance Tuning

| Scenario | Chunk Size | Workers | Retry | Notes |
|----------|-----------|---------|-------|-------|
| Slow WiFi | 1MB | 1 | 5 | More retries for unreliability |
| Fast LAN | 8MB | 4 | 3 | Larger chunks for throughput |
| Mixed | 4MB | 2 | 3 | Balanced default |
| USB only | 4MB | 2 | 3 | Remove WiFi from config |
| Large files | 8MB | 4 | 3 | Optimize for bandwidth |

## Integration with Existing phone.py

The Windows `pc.py` and Termux `phone.py` use the same `HybridLink-Core` engine:

### Synchronized Protocol

- Both use same `TransferController`
- Same chunk structure and headers
- Compatible manifest format
- Cross-compatible resume files

### Launching Phone Receiver

```bash
# On Termux (Android)
cd ~/HybridLink-Core
python phone.py receive 104857600 --output backup.bin

# Or send from Android to PC
python phone.py send large_file.zip --pc 192.168.1.50:9001
```

## Development

### Adding Features

1. **Windows-specific utilities** → `windows_utils.py`
2. **Connection logic** → `windows_connection_manager.py`
3. **Checkpointing** → `manifest_manager.py`
4. **Core transfer logic** → Upstream in `HybridLink-Core/`

### Testing

```powershell
# Test ADB detection
python -m hybridlink_core.windows_utils

# Test manifest manager
python -m hybridlink_core.manifest_manager

# Test connection manager
python -m hybridlink_core.windows_connection_manager
```

## Architecture Decisions

### Why Dual-Channel?

- **USB**: Reliable, consistent latency, wired connection - good for control/metadata
- **WiFi**: Higher throughput, wireless - good for bulk data
- **Combined**: USB handles reliability, WiFi provides bandwidth

### Why Chunks?

- Enables parallel processing on multiple channels
- Allows intelligent scheduling (fast vs slow channels)
- Enables resume without re-transferring entire file
- Reduces memory usage (stream chunks, not full file)

### Why Async/Await?

- Allows monitoring multiple channels concurrently
- Health checks don't block transfers
- Progress updates don't stall transfer operations
- Graceful shutdown and cleanup

## Future Enhancements

- [ ] WebRTC transport for NAT traversal
- [ ] Relay server support
- [ ] Bluetooth as fallback channel
- [ ] File compression in-flight
- [ ] Resumable receive with partial chunks
- [ ] GUI wrapper for non-technical users
- [ ] Linux/macOS optimized builds

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please:
1. Test on Windows CMD and PowerShell
2. Avoid Linux-only dependencies
3. Update documentation
4. Follow existing code style

## Support

- Issues: GitHub Issues
- Wiki: Setup guides and examples
- Q&A: Discussions

---

**Ready to transfer?**

```powershell
python pc.py
```

Enjoy fast, reliable file transfers! 🚀
