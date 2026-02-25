"""
Windows Setup and Configuration Guide for HybridLink

This guide helps you set up the Windows PC side of HybridLink for dual-channel
file transfers using USB (ADB) and WiFi simultaneously.
"""

# Example configuration file: ~/.config/HybridLink/pc_config.json
EXAMPLE_CONFIG = {
    # Device discovery
    "phone_ip": "192.168.1.100",  # Target phone WiFi IP
    "phone_ssh_port": 22,         # SSH port on phone (Termux)
    "phone_transfer_port": 9001,  # Transfer service port on phone
    
    # USB (ADB) forwarding
    "usb_local_port": 9000,       # Local PC port for USB forwarding
    "usb_remote_port": 9001,      # Remote port on Android device
    
    # Transfer settings
    "chunk_size": 4194304,        # 4MB chunks (can be 512KB-2MB for slower networks)
    "max_retries": 3,             # Retry failed chunks this many times
    
    # Features
    "verify_integrity": True,     # Verify SHA256 hash after transfer
    "auto_resume": True,          # Resume interrupted transfers automatically
    
    # Performance
    "usb_enabled": True,          # Enable USB channel
    "wifi_enabled": True,         # Enable WiFi channel
    "parallel_workers": 2,        # Workers per channel
}

# QUICK START
QUICKSTART_STEPS = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    HybridLink Windows Quick Start Guide                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

STEP 1: PREREQUISITES
━━━━━━━━━━━━━━━━━━━━
□ Android device with Termux installed
□ USB cable for ADB connection
□ Python 3.8+ installed on Windows
□ Android SDK Platform Tools (for ADB)

STEP 2: INSTALL ANDROID SDK PLATFORM TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Download: https://developer.android.com/tools/releases/platform-tools
Extract to: C:\\Android\\sdk\\platform-tools

Verify ADB is available:
  > adb --version
  > adb devices

STEP 3: INSTALL HYBRIDLINK
━━━━━━━━━━━━━━━━━━━━━━━━━━
Clone the repository:
  > git clone https://github.com/[YOUR_REPO]/HybridFileShare
  > cd HybridFileShare/HybridLink-Core

Install Python dependencies:
  > pip install -r requirements.txt
  
  # Required packages:
  # - paramiko>=3.0.0 (SSH)
  # - pydantic>=2.0.0 (data validation)
  # - click>=8.0.0 (CLI)
  # - colorama>=0.4.6 (Windows colors)
  # - rich>=13.0.0 (progress bars)

STEP 4: SET UP PHONE SIDE (TERMUX)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
On your Android device:

1. Install Termux and run:
   $ apt update
   $ apt install openssh
   
2. Set SSH password and start server:
   $ passwd  # Set your SSH password
   $ sshd    # Start SSH daemon

3. Get phone IP:
   $ ip addr show | grep inet

4. Start HybridLink receiver:
   $ cd /data/data/com.termux/files/home/HybridLink-Core
   $ python phone.py receive 104857600 --output received.bin

STEP 5: ENABLE ADB OVER USB
━━━━━━━━━━━━━━━━━━━━━━━━━━

Connect phone via USB:
  > adb devices

Ensure it shows "device" (not "offline"):
  > adb devices -l

STEP 6: SEND A FILE FROM WINDOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interactive mode (easiest):
  > python windows-client\\pc.py
  
  Select "1" for Send
  Enter file path when prompted
  Enter phone IP when prompted

Command line mode:
  > python windows-client\\pc.py send "C:\\path\\to\\file.zip" --phone 192.168.1.100

Monitor transfer progress:
  ✓ Progress bar shows combined speed
  ✓ Per-channel speeds displayed
  ✓ USB + WiFi work simultaneously

STEP 7: VERIFY TRANSFER
━━━━━━━━━━━━━━━━━━━━━
On phone (Termux), verify received file:
  $ ls -lh received.bin
  $ sha256sum received.bin

On Windows, should see matching hash in console output.

═══════════════════════════════════════════════════════════════════════════════

USAGE EXAMPLES

📤 SEND FILE (Interactive):
  > cd HybridFileShare
  > python windows-client/pc.py
  [Select option 1]
  [Enter file path]
  [Enter phone IP]

📤 SEND FILE (CLI):
  > python windows-client/pc.py send "D:\\Backups\\database.sql" --phone 192.168.1.100
  
📥 RECEIVE FILE:
  > python windows-client/pc.py receive "D:\\Downloads\\from_phone.bin" \\
      --file-size 536870912 --phone 192.168.1.100

🔧 CONFIGURE DEVICE:
  > python windows-client/pc.py
  [Select option 3]
  [Update phone IP, SSH port, chunk size]

═══════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING

Problem: "ADB not found"
Solution: 
  1. Install Android SDK Platform Tools
  2. Ensure 'adb' is in PATH or in C:\\Android\\sdk\\platform-tools
  3. Verify: adb --version

Problem: "No devices detected"
Solution:
  1. Connect phone via USB
  2. Enable USB debugging on phone
  3. adb devices (should show device)
  4. Grant USB authorization on phone if prompted

Problem: "WiFi connection failed"
Solution:
  1. Verify phone WiFi IP: adb shell ip addr show
  2. Ensure phone and PC on same network
  3. SSH running on phone: ps | grep sshd
  4. Check SSH password is set: ssh [phone_ip]

Problem: "Transfer slow or stalling"
Solution:
  1. Reduce chunk size: --chunk-size 1048576  (1MB)
  2. Check USB cable quality
  3. Monitor: adb shell cat /proc/net/dev
  4. Disable WiFi if USB only needed: config file

Problem: "Transfer interrupted - can resume?"
Solution:
  Run same command again - HybridLink automatically detects
  completed chunks and resumes where it left off.

═══════════════════════════════════════════════════════════════════════════════

PERFORMANCE TUNING

For Fast USB + WiFi (typical):
  "chunk_size": 4194304  (4MB)

For Slow/Unreliable WiFi:
  "chunk_size": 1048576  (1MB)
  "max_retries": 5
  "wifi_enabled": False  (USB only)

For Large Files (>1GB):
  "chunk_size": 8388608  (8MB)
  "parallel_workers": 4

═══════════════════════════════════════════════════════════════════════════════

ARCHITECTURE

Transfer Flow:
  
  PC (Windows)                          Android (Termux)
  ============                          ================
  
  file.bin
     ↓
  [ChunkManager]
     ├─ Chunk 0
     ├─ Chunk 1         ↓ USB (ADB)    [Receiver]
     ├─ Chunk 2    ┌──────────┐        ├─ Chunk 0
     └─ Chunk N    │ TCP 9000 │───────→├─ Chunk 1
                   └──────────┘        └─ Temp Storage
                   
                   ↓ WiFi (SSH)
                   ┌──────────┐
                   │ TCP 9001 │───────→[ChunkAssembler]
                   └──────────┘             ↓
                                       received.bin

Scheduler distributes chunks to fastest channel automatically.

═══════════════════════════════════════════════════════════════════════════════

FAQ

Q: Why dual-channel?
A: USB and WiFi have different reliability/speed profiles. USB is wired (reliable)
   but bandwidth-limited. WiFi is fast but less reliable. Using both simultaneously
   provides optimal throughput and automatic failover.

Q: Can I use WiFi only?
A: Yes - disable USB in config or if ADB not available, WiFi channel used alone.

Q: What happens if a channel fails mid-transfer?
A: Transfer continues on remaining channel(s). Failed chunks are automatically
   retried. Transfer completes successfully as long as one channel works.

Q: How to resume interrupted transfer?
A: Checkpoint file stored in ~/.config/HybridLink/
   Run same send/receive command - automatically resumes from last checkpoint.

Q: Can I modify chunk size mid-transfer?
A: Not recommended - use checkpoint restart with new size instead.

Q: Does it work on macOS/Linux?
A: Yes - same codebase (pc.py) works on all platforms. Windows-specific code
   isolated to windows_utils.py module.

═══════════════════════════════════════════════════════════════════════════════
"""

INTEGRATION_GUIDE = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║              Integrating pc.py with Existing phone.py                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

OVERVIEW
───────
The pc.py (Windows) and phone.py (Termux) are complementary applications that
work together to enable dual-channel transfers. They use the same core engine:
HybridLink-Core

SYNCHRONIZATION
──────────────

1. Both must agree on:
   ✓ Chunk size (4MB default)
   ✓ Total file size
   ✓ Port numbers (USB: 9000, WiFi: 9001)
   ✓ Transfer protocol version

2. Configuration exchange happens via:
   ✓ Handshake on first connection
   ✓ Metadata in chunk headers
   ✓ Checkpoint files for resume

PROTOCOL (Simplified)
────────────────────

SEND MODE:
  PC (Sender)                     Android (Receiver)
  ╔════════════╗                  ╔════════════╗
  │ pc.py send │                  │ phone.py   │
  ╚════════════╝                  ╚════════════╝
       │                               │
       .─────── HANDSHAKE ──────────→  .
       │                               │
       .─────── FILE METADATA ────────→ . (stores .manifest)
       │                               │
       .─────── CHUNK_ID: 0xDEADBEEF ─→ . (receives, stores)
       │                               │
       .─────── ACKNOWLEDGE ←───────── .
       │                               │
       └─── (repeat for each chunk) ──→
       
       .─────── FINALIZE ────────────→
       │                               │
       .─────── HASH_VALUE ──────────→
       │                               │
       .─────── VERIFY_OK ←─────────── . (verifies hash)

RECEIVE MODE:
  PC (Receiver)                   Android (Sender)
  ╔════════════╗                  ╔════════════╗
  │ pc.py recv │                  │ phone.py   │
  ╚════════════╝                  ╚════════════╝
       │                               │
       .─────── REQUEST SIZE ────────→ .
       │                               │
       .─────── FILE_SIZE ←─────────── . (metadata)
       │                               │
       . (allocates chunks) ←────────── .
       │                               │
       .─────── GET_CHUNK: 0 ───────→  .
       │                               │
       .─────── CHUNK_DATA ←────────── . (sends)
       │                               │
       └─── (repeat for each chunk) ───→

CROSS-COMPATIBILITY
──────────────────

✓ SAME CODE: Both use TransferController from HybridLink-Core
✓ SAME MODELS: Both use models.py for data structures
✓ SAME SCHEDULER: Both use multichannel_scheduler.py

Differences:
  ├─ Windows utilities (windows_utils.py) - PC only
  ├─ Phone utilities (phone_discovery.py) - Phone only
  └─ Connection managers - Platform-specific transport

FILE MERGE
─────────

PC (receive mode):
  ChunkAssembler.assemble() - reads chunks in order, writes to destination

Phone (receive mode):
  ChunkAssembler.assemble() - same logic, different temp location

Both validate:
  ✓ Chunk ordering
  ✓ File hash (SHA256)
  ✓ Byte count

INTERRUPT/RESUME
────────────────

Manifest file location (transferred via protocol):
  
  PC:    ~/.config/HybridLink/.hybridlink_TRANSFER-ID.manifest
  Phone: /data/data/com.termux/files/home/.hybridlink_TRANSFER-ID.manifest

Resume logic:
  1. pc.py/phone.py loads manifest
  2. Detects completed chunks
  3. Requests only pending chunks
  4. Continues until complete

ADDING NEW FEATURES
──────────────────

To add a feature available on both platforms:

1. Add to core HybridLink-Core module (common code)
2. Add platform-specific wrappers in:
   - windows_utils.py (Windows)
   - phone_discovery.py (Termux)
   - connection manager modules
3. Update transfer_controller.py to use new feature
4. Both pc.py and phone.py inherit the feature automatically

Example: Adding Bluetooth channel
  
  1. Create bluetooth_transport.py in HybridLink-Core/
  2. Register in ChannelManager
  3. Both pc.py and phone.py can use it without changes

═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(QUICKSTART_STEPS)
    print("\n\n")
    print(INTEGRATION_GUIDE)
