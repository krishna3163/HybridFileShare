# HybridLink-Core API Reference

Complete API documentation for all modules and classes in HybridLink-Core.

## Table of Contents

1. [TransferController](#transfercontroller)
2. [ChunkManager](#chunkmanager)
3. [ChannelManager](#channelmanager)
4. [Transport Layer](#transport-layer)
5. [MultiChannelScheduler](#multichannelscheduler)
6. [ChunkAssembler](#chunkassembler)
7. [IntegrityVerifier](#integrityverifier)
8. [ProgressReporter](#progressreporter)
9. [Models](#models)
10. [Configuration](#configuration)

---

## TransferController

Main orchestrator for file transfers.

### Constructor

```python
TransferController(config: Optional[TransferConfig] = None) -> TransferController
```

Creates a new transfer controller with optional configuration.

**Parameters:**
- `config`: Transfer configuration (uses defaults if None)

**Example:**
```python
from hybridlink_core import TransferController, TransferConfig

config = TransferConfig(chunk_size=8*1024*1024)
controller = TransferController(config)
```

### Methods

#### initialize_sender()

```python
async def initialize_sender(
    file_path: Path,
    destination_host: str,
    transfer_id: str = ""
) -> bool
```

Initialize sender mode for sending a file.

**Parameters:**
- `file_path`: Path to file to send
- `destination_host`: Destination IP/hostname (for WiFi)
- `transfer_id`: Optional transfer identifier

**Returns:** `bool` - True if initialization successful

**Raises:** 
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If configuration invalid

**Example:**
```python
success = await controller.initialize_sender(
    Path("myfile.zip"),
    "192.168.1.100"
)
```

#### initialize_receiver()

```python
async def initialize_receiver(
    destination_path: Path,
    file_size: int,
    transfer_id: str = ""
) -> bool
```

Initialize receiver mode for receiving a file.

**Parameters:**
- `destination_path`: Where to save received file
- `file_size`: Total size of incoming file (bytes)
- `transfer_id`: Optional transfer identifier

**Returns:** `bool` - True if initialization successful

**Example:**
```python
success = await controller.initialize_receiver(
    Path("received_file.zip"),
    file_size=104857600  # 100 MB
)
```

#### connect_channels()

```python
async def connect_channels() -> bool
```

Connect all available transport channels.

**Returns:** `bool` - True if at least one channel connected

**Raises:**
- Logs warnings for channels that fail to connect

**Example:**
```python
if not await controller.connect_channels():
    print("No channels available")
```

#### send()

```python
async def send() -> bool
```

Execute the send transfer operation.

**Returns:** `bool` - True if transfer completed successfully

**Prerequisites:**
- Must call `initialize_sender()` first
- Must call `connect_channels()` first

**Example:**
```python
result = await controller.send()
if result:
    print("Transfer successful")
```

#### receive()

```python
async def receive() -> bool
```

Execute the receive transfer operation.

**Returns:** `bool` - True if transfer completed successfully

**Prerequisites:**
- Must call `initialize_receiver()` first
- Must call `connect_channels()` first

**Example:**
```python
result = await controller.receive()
```

#### shutdown()

```python
async def shutdown() -> None
```

Gracefully shutdown the transfer.

Cancels active operations, disconnects channels, and cleans up resources.

**Example:**
```python
try:
    await controller.send()
except KeyboardInterrupt:
    await controller.shutdown()
```

#### set_progress_callback()

```python
def set_progress_callback(callback: Callable[[ProgressUpdate], None]) -> None
```

Set a callback for progress updates.

**Parameters:**
- `callback`: Function called on each progress update

**Example:**
```python
def on_progress(update: ProgressUpdate):
    print(f"Progress: {update.progress_percent:.1f}%")

controller.set_progress_callback(on_progress)
```

#### get_status()

```python
def get_status() -> dict
```

Get current transfer status.

**Returns:** `dict` with keys:
- `state`: Current transfer state
- `mode`: SEND or RECEIVE
- `chunk_manager`: Chunk statistics
- `progress`: Progress information
- `channels`: Channel statistics

**Example:**
```python
status = controller.get_status()
print(f"State: {status['state']}")
print(f"Progress: {status['progress']['progress_percent']:.1f}%")
```

---

## ChunkManager

Manages file chunking and state tracking.

### Constructor

```python
ChunkManager(chunk_size: int = DEFAULT_CHUNK_SIZE) -> ChunkManager
```

**Parameters:**
- `chunk_size`: Size of each chunk in bytes (default: 4MB)

**Example:**
```python
from hybridlink_core import ChunkManager

manager = ChunkManager(chunk_size=8*1024*1024)  # 8 MB chunks
```

### Methods

#### initialize_file()

```python
def initialize_file(file_path: Path, transfer_id: str = "") -> None
```

Initialize chunking for a file.

**Parameters:**
- `file_path`: Path to file
- `transfer_id`: Optional transfer identifier

**Raises:** `FileNotFoundError` if file doesn't exist

#### get_chunk_data()

```python
def get_chunk_data(chunk_id: int) -> bytes
```

Read chunk data from file.

**Parameters:**
- `chunk_id`: ID of chunk to read

**Returns:** `bytes` - Raw chunk data

**Raises:** 
- `ValueError`: If chunk_id invalid
- `FileNotFoundError`: If file no longer exists

#### mark_transferred()

```python
def mark_transferred(chunk_id: int, hash_value: Optional[str] = None) -> None
```

Mark a chunk as successfully transferred.

**Parameters:**
- `chunk_id`: ID of chunk
- `hash_value`: Optional hash for verification

#### mark_failed()

```python
def mark_failed(chunk_id: int) -> None
```

Mark transfer attempt as failed (increments counter).

#### get_pending_chunks()

```python
def get_pending_chunks() -> List[ChunkInfo]
```

Get list of untransferred chunks.

**Returns:** `List[ChunkInfo]` - Pending chunks

#### get_transfer_progress()

```python
def get_transfer_progress() -> tuple[int, int]
```

Get transfer progress.

**Returns:** `(chunks_transferred, total_chunks)`

#### get_statistics()

```python
def get_statistics() -> dict
```

Get detailed chunk statistics.

**Returns:** `dict` with keys:
- `total_chunks`: Total number of chunks
- `chunks_transferred`: Already transferred
- `bytes_transferred`: Bytes transferred
- `completion_percent`: Percentage complete

---

## ChannelManager

Manages USB and WiFi transport channels.

### Constructor

```python
ChannelManager() -> ChannelManager
```

**Example:**
```python
from hybridlink_core import ChannelManager

manager = ChannelManager()
```

### Methods

#### register_channel()

```python
def register_channel(channel_type: str, transport: TransportBase) -> None
```

Register a transport channel.

**Parameters:**
- `channel_type`: Type identifier (e.g., "usb", "wifi")
- `transport`: Transport instance

**Example:**
```python
from hybridlink_core.usb_transport import UsbTransport

usb = UsbTransport()
manager.register_channel("usb", usb)
```

#### connect_channel()

```python
async def connect_channel(channel_type: str) -> bool
```

Connect a specific channel.

**Parameters:**
- `channel_type`: Type of channel to connect

**Returns:** `bool` - True if connected

#### disconnect_channel()

```python
async def disconnect_channel(channel_type: str) -> None
```

Disconnect a specific channel.

#### disconnect_all()

```python
async def disconnect_all() -> None
```

Disconnect all channels.

#### is_channel_available()

```python
async def is_channel_available(channel_type: str) -> bool
```

Check if channel is connected and available.

#### get_available_channels()

```python
async def get_available_channels() -> List[str]
```

Get list of available channel types.

#### get_fastest_channel()

```python
def get_fastest_channel() -> Optional[str]
```

Get the fastest available channel by recent measurements.

**Returns:** `str` - Channel type, or None if none available

#### record_transfer()

```python
def record_transfer(
    channel_type: str,
    bytes_transferred: int,
    error: Optional[str] = None
) -> None
```

Record a transfer event on a channel.

#### get_channel_stats()

```python
def get_channel_stats(channel_type: str) -> Optional[ChannelStats]
```

Get statistics for a channel.

#### get_summary()

```python
def get_summary() -> dict
```

Get summary of all channels.

---

## Transport Layer

Base class and implementations for USB and WiFi.

### TransportBase (Abstract)

```python
class TransportBase(ABC):
    @abstractmethod
    async def connect(self) -> bool: ...
    
    @abstractmethod
    async def disconnect(self) -> None: ...
    
    @abstractmethod
    async def is_connected(self) -> bool: ...
    
    @abstractmethod
    async def send_chunk(self, chunk_data: bytes, chunk_id: int) -> Tuple[bool, int]: ...
    
    @abstractmethod
    async def receive_chunk(self) -> Optional[bytes]: ...
    
    @abstractmethod
    async def measure_speed(self) -> float: ...
```

### UsbTransport

```python
class UsbTransport(TransportBase):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        config: Optional[TransportConfig] = None
    ) -> UsbTransport
```

USB transport using ADB TCP forwarding.

**Parameters:**
- `host`: Host address (default: localhost)
- `port`: Port number (default: 9000 - matches `adb forward`)
- `config`: Transport configuration

**Example:**
```python
from hybridlink_core.usb_transport import UsbTransport

usb = UsbTransport(host="localhost", port=9000)
await usb.connect()
```

### WifiTransport

```python
class WifiTransport(TransportBase):
    def __init__(
        self,
        host: str,
        port: int = 9001,
        config: Optional[TransportConfig] = None
    ) -> WifiTransport
```

WiFi transport using native TCP sockets.

**Parameters:**
- `host`: Android device IP or hostname
- `port`: Port number (default: 9001)
- `config`: Transport configuration

**Example:**
```python
from hybridlink_core.wifi_transport import WifiTransport

wifi = WifiTransport(host="192.168.1.100")
await wifi.connect()
```

---

## MultiChannelScheduler

Intelligent chunk scheduling across channels.

### Constructor

```python
MultiChannelScheduler(
    chunk_manager: ChunkManager,
    channel_manager: ChannelManager,
    max_retries: int = 3
) -> MultiChannelScheduler
```

**Example:**
```python
scheduler = MultiChannelScheduler(chunk_manager, channel_manager)
await scheduler.initialize()
```

### Methods

#### schedule_transfers()

```python
async def schedule_transfers(
    concurrent_transfers: int = 2
) -> Dict[str, List[ChunkRequest]]
```

Schedule chunks across available channels.

**Parameters:**
- `concurrent_transfers`: Max concurrent transfers per channel

**Returns:** `Dict` mapping channel_type to list of ChunkRequest

#### handle_chunk_success()

```python
async def handle_chunk_success(
    chunk_id: int,
    bytes_transferred: int,
    channel_type: str
) -> None
```

Handle successful chunk transfer.

#### handle_chunk_failure()

```python
async def handle_chunk_failure(
    chunk_id: int,
    channel_type: str,
    error: str = ""
) -> bool
```

Handle failed chunk transfer.

**Returns:** `bool` - True if chunk will be retried

#### get_failed_chunks()

```python
def get_failed_chunks() -> List[int]
```

Get list of chunks that failed all retries.

---

## ChunkAssembler

Assembles received chunks into final file.

### Constructor

```python
ChunkAssembler(
    output_path: Path,
    total_size: int,
    chunk_size: int
) -> ChunkAssembler
```

**Parameters:**
- `output_path`: Where to write final file
- `total_size`: Total file size (bytes)
- `chunk_size`: Individual chunk size

**Example:**
```python
from hybridlink_core.chunk_assembler import ChunkAssembler

assembler = ChunkAssembler(
    Path("output.bin"),
    total_size=104857600,
    chunk_size=4*1024*1024
)
```

### Methods

#### write_chunk()

```python
def write_chunk(chunk_id: int, chunk_data: bytes) -> bool
```

Write a received chunk to temporary storage.

**Parameters:**
- `chunk_id`: ID of chunk
- `chunk_data`: Raw chunk data

**Returns:** `bool` - False if duplicate chunk

#### verify_and_mark_chunk()

```python
def verify_and_mark_chunk(
    chunk_id: int,
    expected_hash: Optional[str] = None
) -> bool
```

Verify and mark chunk as verified.

#### assemble_file()

```python
def assemble_file(verify_final: bool = True) -> bool
```

Assemble all chunks into final file.

**Parameters:**
- `verify_final`: Whether to verify final file hash

**Returns:** `bool` - True if assembly successful

#### get_pending_chunks()

```python
def get_pending_chunks() -> list
```

Get list of chunks not yet received.

#### cleanup()

```python
def cleanup() -> None
```

Clean up temporary files.

---

## IntegrityVerifier

Verifies data integrity using SHA-256.

### Static Methods

#### hash_bytes()

```python
@staticmethod
def hash_bytes(data: bytes) -> str
```

Calculate SHA-256 hash of bytes.

**Returns:** Hex-encoded hash string

#### hash_file()

```python
@staticmethod
def hash_file(file_path: Path, chunk_size: int = 4*1024*1024) -> str
```

Calculate SHA-256 hash of entire file.

**Parameters:**
- `file_path`: Path to file
- `chunk_size`: Size of chunks to read

**Returns:** Hex-encoded hash string

#### verify_file()

```python
@staticmethod
def verify_file(file_path: Path, expected_hash: str) -> bool
```

Verify file against expected hash.

**Parameters:**
- `file_path`: Path to file
- `expected_hash`: Expected SHA-256 hash

**Returns:** `bool` - True if hash matches

---

## ProgressReporter

Tracks and reports transfer progress.

### Constructor

```python
ProgressReporter(
    transfer_id: str,
    total_bytes: int,
    chunk_manager: ChunkManager,
    channel_manager: ChannelManager
) -> ProgressReporter
```

**Example:**
```python
from hybridlink_core.progress_reporter import ProgressReporter

reporter = ProgressReporter(
    transfer_id="tx_123",
    total_bytes=104857600,
    chunk_manager=chunk_manager,
    channel_manager=channel_manager
)
```

### Methods

#### add_callback()

```python
def add_callback(callback: Callable[[ProgressUpdate], None]) -> None
```

Add a progress callback.

#### update_progress()

```python
def update_progress(
    bytes_transferred: int,
    state: str = "transferring"
) -> ProgressUpdate
```

Update progress and trigger callbacks.

**Returns:** `ProgressUpdate` with current metrics

#### get_status()

```python
def get_status() -> dict
```

Get detailed status information.

#### format_progress_bar()

```python
def format_progress_bar(width: int = 40, show_percent: bool = True) -> str
```

Format a text-based progress bar.

#### format_speed()

```python
def format_speed() -> str
```

Format current speed as human-readable string.

---

## Models

Pydantic data models for type-safe operations.

### ChunkInfo

```python
class ChunkInfo(BaseModel):
    chunk_id: int
    offset: int
    size: int
    hash: Optional[str] = None
    transferred: bool = False
    attempts: int = 0
```

### ChannelStats

```python
class ChannelStats(BaseModel):
    channel_type: str
    available: bool = False
    bytes_transferred: int = 0
    transfer_speed_mbps: float = 0.0
    last_activity: Optional[str] = None
    error_count: int = 0
```

### TransferMetadata

```python
class TransferMetadata(BaseModel):
    transfer_id: str
    file_path: str
    file_size: int
    total_chunks: int
    chunk_size: int
    chunks_transferred: Dict[int, bool] = {}
    start_time: str
    last_updated: str
    mode: str  # "send" or "receive"
    destination_path: Optional[str] = None
    file_hash: Optional[str] = None
    verified_chunks: List[int] = []
```

### TransferConfig

```python
class TransferConfig(BaseModel):
    chunk_size: int = 4 * 1024 * 1024
    max_retries: int = 3
    usb_enabled: bool = True
    wifi_enabled: bool = True
    usb_host: str = "localhost"
    usb_port: int = 9000
    wifi_port: int = 9001
    wifi_timeout: float = 30.0
    channel_timeout: float = 60.0
    verify_integrity: bool = True
```

### ProgressUpdate

```python
class ProgressUpdate(BaseModel):
    transfer_id: str
    bytes_transferred: int
    total_bytes: int
    elapsed_seconds: float
    chunks_completed: int
    total_chunks: int
    current_speed_mbps: float
    eta_seconds: Optional[int] = None
    channels: Dict[str, ChannelStats] = {}
    state: str = "transferring"
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
```

---

## Configuration

Configuration constants and helpers.

### Config Module

```python
# Default sizes
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB

# USB transport
USB_DEFAULT_HOST = "localhost"
USB_DEFAULT_PORT = 9000

# WiFi transport
WIFI_DEFAULT_PORT = 9001
WIFI_TIMEOUT = 30.0

# Timeouts
CHANNEL_TIMEOUT = 60.0
CHUNK_SEND_TIMEOUT = 120.0

# Retry policy
MAX_RETRIES = 3
RETRY_DELAY = 1.0
```

### Functions

#### get_config_dir()

```python
def get_config_dir() -> Path
```

Get platform-specific configuration directory.

**Returns:** `Path` to config directory
- Windows: `C:\Users\<user>\AppData\Local\HybridLink`
- macOS: `~/Library/Application Support/HybridLink`
- Linux: `~/.config/hybridlink`

---

## CLI Command Reference

See `hybridlink --help` for command-line interface.

```bash
hybridlink send <file>        # Send file
hybridlink receive <dest>     # Receive file
hybridlink configure          # Configure settings
hybridlink status             # Show status
```

---

## Examples

See `examples/` directory for complete working examples:

- `example_sender.py` - Comprehensive send example
- `example_receiver.py` - Comprehensive receive example
- `example_resumable_transfer.py` - Checkpoint and resume
