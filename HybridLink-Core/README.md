# HybridLink-Core: Cross-Platform Multipath Transfer Engine

A production-ready Python transfer engine for simultaneous file transfers over USB (via ADB TCP forwarding) and WiFi, designed for cross-platform support (Windows, macOS, Linux).

## Features

🚀 **Multipath Transfer**
- Simultaneous transfer over USB and WiFi
- Intelligent channel scheduling to fastest available path
- Automatic channel failover and load balancing

📊 **Smart Scheduling**
- Per-channel throughput measurement
- Dynamic chunk assignment based on channel speed
- Automatic retry with exponential backoff

✅ **Reliability**
- SHA-256 integrity verification
- Resumable transfers with checkpoint support
- Prevent duplicate chunk writes
- Graceful shutdown with cleanup

🔄 **Bidirectional**
- Send files from PC to Android
- Receive files from Android to PC
- Same engine for both directions

## Architecture

```
┌─────────────────────────────────────────┐
│         TransferController              │
│  (Orchestrates entire transfer)         │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼──────┐   ┌──────▼─────┐
│  ChunkMgr  │   │ ChannelMgr  │
│  (Files)   │   │  (USB/WiFi) │
└─────┬──────┘   └──────┬──────┘
      │                 │
      └────────┬────────┘
               │
       ┌───────▼────────┐
       │ MultiChannel   │
       │ Scheduler      │
       └───────┬────────┘
               │
      ┌────────┴─────────┐
      │                  │
  ┌───▼────┐       ┌─────▼──┐
  │ USB    │       │ WiFi   │
  │ Trans  │       │ Trans  │
  └────────┘       └────────┘
```

## Core Modules

### ChunkManager
- Splits files into indexed chunks (default 4MB)
- Maintains chunk state map
- Tracks transfer progress

### ChannelManager  
- Manages USB and WiFi channels as independent pipes
- Detects channel availability
- Measures per-channel throughput
- Provides load balancing

### MultiChannelScheduler
- Assigns chunks dynamically to fastest channel
- Implements retry logic for failed chunks
- Continues transfer if one channel disconnects
- Load balances across multiple channels

### UsbTransport
- ADB TCP forwarding (localhost:9000)
- Treats localhost socket as USB pipe
- Binary chunk protocol

### WifiTransport
- Native TCP sockets to Android device
- Configurable port (default 9001)
- Binary chunk protocol

### ChunkAssembler
- Single-writer buffered merge pattern
- Resumable using metadata index
- Prevents duplicate writes
- Manages temporary files

### IntegrityVerifier
- SHA-256 verification for chunks
- Full file verification
- Optional integrity checks

### TransferController
- High-level transfer orchestration
- Bidirectional (send/receive)
- Progress tracking
- Signal handling for graceful shutdown

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/HybridLink-Core.git
cd HybridLink-Core
pip install -e .

# Or install requirements only
pip install -r requirements.txt
```

## Quick Start

### CLI Usage

#### Send a file
```bash
# Send file to Android device (IP: 192.168.1.100)
hybridlink send /path/to/file.zip --host 192.168.1.100

# With options
hybridlink send file.zip --host 192.168.1.100 --chunk-size 8388608 --no-verify
```

#### Receive a file
```bash
# Receive file from Android device (100 MB file)
hybridlink receive /path/to/destination.zip --file-size 104857600

# With options  
hybridlink receive destination.zip --file-size 104857600 --chunk-size 8388608
```

#### Check status
```bash
hybridlink status
```

### Python API

#### Send a file
```python
import asyncio
from pathlib import Path
from hybridlink_core import TransferController
from hybridlink_core.models import TransferConfig

async def main():
    # Configure transfer
    config = TransferConfig(
        chunk_size=4 * 1024 * 1024,  # 4 MB
        usb_enabled=True,
        wifi_enabled=True,
        verify_integrity=True,
    )
    
    # Create controller
    controller = TransferController(config)
    
    # Initialize sender
    await controller.initialize_sender(
        file_path=Path("large_file.zip"),
        destination_host="192.168.1.100",
    )
    
    # Connect channels
    await controller.connect_channels()
    
    # Setup progress callback
    def on_progress(update):
        print(f"Progress: {update.progress_percent:.1f}%")
    
    controller.set_progress_callback(on_progress)
    
    # Run transfer
    success = await controller.run_transfer(controller.send())
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print("✓ Success" if result else "✗ Failed")
```

#### Receive a file
```python
import asyncio
from pathlib import Path
from hybridlink_core import TransferController
from hybridlink_core.models import TransferConfig

async def main():
    config = TransferConfig(
        chunk_size=4 * 1024 * 1024,
        usb_enabled=True,
        wifi_enabled=True,
    )
    
    controller = TransferController(config)
    
    await controller.initialize_receiver(
        destination_path=Path("received_file.zip"),
        file_size=104857600,  # 100 MB
    )
    
    await controller.connect_channels()
    
    success = await controller.run_transfer(controller.receive())
    return success

asyncio.run(main())
```

## Configuration

### Default Settings

```python
# Chunk size: 4 MB
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024

# USB (ADB TCP forwarding)
USB_HOST = "localhost"
USB_PORT = 9000

# WiFi
WIFI_PORT = 9001
WIFI_TIMEOUT = 30.0

# Transfer settings
CHANNEL_TIMEOUT = 60.0
MAX_RETRIES = 3

# Progress reporting
PROGRESS_UPDATE_INTERVAL = 0.5  # seconds
```

### Custom Configuration

```python
from hybridlink_core.models import TransferConfig

config = TransferConfig(
    chunk_size=8 * 1024 * 1024,      # 8 MB chunks
    max_retries=5,                    # Retry up to 5 times
    usb_enabled=True,
    wifi_enabled=True,
    usb_host="localhost",
    usb_port=9000,
    wifi_port=9001,
    wifi_timeout=45.0,
    channel_timeout=90.0,
    verify_integrity=True,
)
```

## Network Protocol

### Binary Chunk Protocol

Each chunk transfer follows this format:

```
[Header: 8 bytes] [Data: variable]
├── Chunk ID (4 bytes, big-endian)
├── Size (4 bytes, big-endian)
└── Data (size bytes)
```

Example:
```
Chunk 0: 0x00 0x00 0x00 0x00 0x00 0x40 0x00 0x00 [4MB of data]
Chunk 1: 0x00 0x00 0x00 0x01 0x00 0x40 0x00 0x00 [4MB of data]
```

## Examples

See the `examples/` directory:

- `example_sender.py` - Send a file
- `example_receiver.py` - Receive a file
- `example_resumable_transfer.py` - Checkpoint and resume support

```bash
# Run examples
python examples/example_sender.py
python examples/example_receiver.py
python examples/example_resumable_transfer.py
```

## Process Flow

### Send Flow
1. **Initialization**
   - Chunk file into fixed-size parts
   - Create metadata
   
2. **Channel Connection**
   - Connect USB (ADB TCP) if available
   - Connect WiFi if available
   
3. **Scheduling**
   - Measure channel speeds
   - Assign chunks to fastest channels
   
4. **Transfer**
   - Send chunks in parallel
   - Monitor progress and errors
   - Retry failed chunks
   
5. **Completion**
   - Verify file integrity
   - Cleanup temporary files
   - Report success/failure

### Receive Flow
1. **Initialization**
   - Create temporary storage
   - Prepare assembler
   
2. **Channel Setup**
   - Listen on USB endpoint
   - Listen on WiFi endpoint
   
3. **Reception**
   - Receive chunks from channels
   - Write to temporary storage
   - Track received chunks
   
4. **Assembly**
   - Merge chunks in order
   - Verify integrity
   - Write final file
   
5. **Cleanup**
   - Remove temporary files
   - Report completion

## Resumable Transfers

### Creating Checkpoints

```python
def on_progress(update):
    # Save checkpoint every 50MB
    if update.bytes_transferred % (50 * 1024 * 1024) == 0:
        controller.metadata_file.write_text(
            json.dumps({
                'transfer_id': update.transfer_id,
                'bytes_transferred': update.bytes_transferred,
                'chunks_completed': update.chunks_completed,
                'timestamp': time.time(),
            })
        )

controller.set_progress_callback(on_progress)
```

### Resuming Transfers

```python
import json

# Load checkpoint
checkpoint = json.loads(Path(".transfer_checkpoint").read_text())

# Resume from checkpoint
# (Implementation depends on checkpoint data)
```

## Performance Tuning

### For Large Files (> 1 GB)

```python
config = TransferConfig(
    chunk_size=16 * 1024 * 1024,  # Increase to 16 MB
    channel_timeout=120.0,         # Increase timeout
    max_retries=5,                 # More retries
)
```

### For Many Small Files

```python
config = TransferConfig(
    chunk_size=1 * 1024 * 1024,    # Small chunks (1 MB)
    usb_enabled=True,
    wifi_enabled=True,
)
```

### For Slow Networks

```python
config = TransferConfig(
    chunk_size=2 * 1024 * 1024,    # Smaller chunks
    channel_timeout=180.0,          # Longer timeout
    wifi_timeout=60.0,              # Longer WiFi timeout
)
```

## Troubleshooting

### USB Connection Issues

1. Ensure ADB is installed: `adb --version`
2. Forward USB port: `adb forward tcp:9000 tcp:9000`
3. Verify device connected: `adb devices`

```bash
# Setup ADB forwarding
adb forward tcp:9000 tcp:9000

# Verify connection
adb shell netstat | grep 9000
```

### WiFi Connection Issues

1. Ensure Android device is on same network
2. Get Android device IP: `adb shell ip addr show wlan0`
3. Verify connectivity: `ping <device_ip>`

### Transfer Hangs

1. Check channel health: Monitor speed measurements
2. Increase timeout values in config
3. Check network connectivity
4. Reduce chunk size for more granular progress

### Performance Issues

1. Monitor per-channel speed measurements
2. Check for errors in logs: `LOG_LEVEL=DEBUG`
3. Verify USB bandwidth (USB 2.0 = ~60 Mbps, USB 3.0 = ~400 Mbps)
4. Verify WiFi bandwidth: `speedtest` or similar

## Security Considerations

- No encryption by default (run on trusted networks)
- SHA-256 verification ensures data integrity
- Implement TLS for untrusted networks:

```python
# Custom transport with TLS (requires paramiko)
class SecureUsbTransport(UsbTransport):
    async def connect(self):
        # Implement TLS handshake
        pass
```

## Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure per module
logging.getLogger("hybridlink_core").setLevel(logging.DEBUG)
```

## Development

### Running Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=hybridlink_core
```

### Code Style

```bash
# Format code with black
black hybridlink_core/

# Lint with pylint
pylint hybridlink_core/

# Type check with mypy
mypy hybridlink_core/
```

### Building

```bash
# Build package
python -m build

# Install locally in dev mode
pip install -e ".[dev]"
```

## Architecture for Rust Migration

The codebase is designed to be easily portable to Rust:

1. **Module Structure**: Each module can be independently ported
2. **Trait-based Design**: Abstract base classes → Rust traits
3. **Async/Await**: Already using asyncio, maps to async/await in Rust
4. **Type Safety**: Pydantic models → Rust structs with validation
5. **Binary Protocol**: Language-agnostic protocol definition

See `RUST_MIGRATION.md` for detailed porting guide.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

- 📖 Documentation: See `docs/` directory
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: support@hybridlink.org

## Roadmap

- [ ] Rust implementation
- [ ] Web UI for progress monitoring
- [ ] Multi-device support
- [ ] Bandwidth limiting
- [ ] End-to-end encryption
- [ ] Compression support
- [ ] Directory synchronization
- [ ] Delta sync for repeated transfers

## Acknowledgments

Built by the HybridLink team for efficient multipath file transfers.
