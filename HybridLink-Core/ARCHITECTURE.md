# HybridLink-Core Architecture

## System Overview

HybridLink-Core is a cross-platform multipath file transfer engine designed to efficiently transfer files between PCs and Android devices over both USB (via ADB) and WiFi simultaneously.

```
    ┌─────────────┐
    │   User      │
    │   (CLI)     │
    └──────┬──────┘
           │
    ┌──────▼─────────────────┐
    │ TransferController     │
    │ (Main Orchestrator)    │
    └──────┬─────────────────┘
           │
      ┌────┴─────────────────┬──────────────────┐
      │                      │                  │
   ┌──▼──────────┐   ┌───────▼────────┐  ┌─────▼──────┐
   │ChunkManager │   │ChannelManager  │  │  Scheduler │
   │ (Files)    │   │  (Pipes)       │  │ (Logic)    │
   └──┬─────────┘   └┬───────────────┘  └──┬────┬────┘
      │              │                      │    │
      │         ┌────┴──────────┐           │    │
      │         │               │           │    │
   ┌──▼──┐  ┌───▼──┐       ┌────▼──┐   ┌───▼┐ ┌▼──┐
   │ File│  │ USB  │─ADB─  │Device │   │USB │ │WiFi│
   │ I/O │  │ Tran │   FWD  │ (Recv)│   │Tran│ │Tran│
   └─────┘  └──────┘       └───────┘   └────┘ └────┘
   
           WiFi ├─ Direct TCP ─┤ WiFi
```

## Core Design Principles

### 1. **Separation of Concerns**
Each module has a single responsibility:

- **ChunkManager**: File splitting and state tracking
- **ChannelManager**: Transport layer abstraction
- **MultiChannelScheduler**: Selection and load balancing
- **TransportBase/USB/WiFi**: Network communication
- **ChunkAssembler**: Fragment reassembly
- **IntegrityVerifier**: Data validation
- **ProgressReporter**: User feedback
- **TransferController**: Orchestration

### 2. **Abstraction Layers**

```
Layer 0: OS/Network (sockets, ADB)
Layer 1: Transport (USB, WiFi)
Layer 2: Channel Management (health, speed)
Layer 3: Scheduling (assignment, retry)
Layer 4: Transfer Logic (send/receive)
Layer 5: User Interface (CLI, progress)
```

### 3. **State Machine Pattern**

```
IDLE
  ↓
PREPARING (Initialize components)
  ↓
TRANSFERRING (Active transfer)
  ├→ PAUSED (Optional, if interrupted)
  │    ↓ (Resume)
  └→ COMPLETED (Success)
  
  ↓ (On error)
  FAILED (Transfer unsuccessful)
```

### 4. **Async-First Design**

All I/O operations are async:

```python
# Network I/O
async def send_chunk(data, chunk_id)
async def receive_chunk()

# Concurrent operations
asyncio.gather(
    channel1.send_chunk(...),
    channel2.send_chunk(...),
    channel3.measure_speed(),
)

# Task scheduling
await scheduler.schedule_transfers()
await channel_health_monitor()
```

### 5. **Type Safety (Runtime)**

Using Pydantic for data validation:

```python
# Runtime validation
update = ProgressUpdate(
    transfer_id="tx_123",
    bytes_transferred=1024,  # Must be int
    # ... validation happens automatically
)
```

## Data Flow Architecture

### Send Flow

```
┌──────────────────────────────────────────────────────────┐
│                    File to Transfer                       │
└────────────────┬─────────────────────────────────────────┘

                 │ ChunkManager.initialize_file()
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Chunks Created (metadata, state tracking)                 │
│  ├─ Chunk 0: [0, 4MB)        -> transferred: False       │
│  ├─ Chunk 1: [4MB, 8MB)      -> transferred: False       │
│  ├─ Chunk 2: [8MB, 12MB)     -> transferred: False       │
│  └─ ...up to N chunks         -> transferred: False      │
└────────────────┬─────────────────────────────────────────┘

                 │ ChannelManager.connect_channel()
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Channels Connected (speed measurement started)            │
│  ├─ USB: connected=True, speed=150 Mbps                  │
│  └─ WiFi: connected=True, speed=200 Mbps                 │
└────────────────┬─────────────────────────────────────────┘

                 │ MultiChannelScheduler.schedule_transfers()
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Chunks Assigned to Channels (fastest first)              │
│  ├─ Chunk 0 → WiFi (fastest)                            │
│  ├─ Chunk 1 → WiFi                                       │
│  ├─ Chunk 2 → USB (second)                              │
│  └─ Chunk 3 → USB                                        │
└────────────────┬─────────────────────────────────────────┘

                 │ TransportBase.send_chunk()
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Transfer in Progress (parallel on different channels)     │
│  ├─ WiFi   → Sending Chunk 0 (progress: 50%)            │
│  ├─ USB    → Sending Chunk 2 (progress: 25%)            │
│  └─ Both   → Continuous speed measurement               │
└────────────────┬─────────────────────────────────────────┘

                 │ Scheduler decisions continuously
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Dynamic Reallocation (if channel becomes slow/fails)     │
│  Original: Chunk 3 → USB (was slow)                      │
│  Updated:  Chunk 3 → WiFi (now faster)                   │
└────────────────┬─────────────────────────────────────────┘

                 │ All chunks → ChunkManager.mark_transferred()
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Transfer Complete (all chunks marked transferred)         │
│  ├─ File integrity verified (SHA-256)                    │
│  ├─ Statistics collected                                 │
│  └─ Cleanup performed                                    │
└────────────────┬─────────────────────────────────────────┘

                 │ TransferController → COMPLETED
                 ▼
              SUCCESS
```

### Receive Flow

```
┌──────────────────────────────────────────────────────────┐
│          Android Device (Source)                          │
│        Sending chunks via USB+WiFi                        │
└────────────────┬─────────────────────────────────────────┘

                 │ ChunkAssembler initialization
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Temporary Storage Created                                 │
│  └─ /tmp/hybridlink_XXXXX/                              │
│     ├─ chunk_000000.tmp                                  │
│     ├─ chunk_000001.tmp                                  │
│     └─ .checkpoint (metadata)                            │
└────────────────┬─────────────────────────────────────────┘

                 │ Channels listen for incoming data
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Chunks Received (stored in temp, may arrive out of order)│
│  ├─ USB: Received Chunk 2 (4MB)                         │
│  ├─ WiFi: Received Chunk 0 (4MB)                        │
│  ├─ WiFi: Received Chunk 1 (4MB)                        │
│  └─ Continue until all received                         │
└────────────────┬─────────────────────────────────────────┘

                 │ ChunkAssembler.write_chunk()
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Chunks Written to Temp Files                              │
│  ├─ Prevented duplicate writes                           │
│  ├─ Calculated SHA-256 per chunk                         │
│  └─ Saved checkpoint for resumption                      │
└────────────────┬─────────────────────────────────────────┘

                 │ All chunks received?
                 ├─ YES → ChunkAssembler.assemble_file()
                 ▼
┌────────────────────────────────────────────────────────────┐
│ File Assembly (ordered merge)                             │
│  ├─ Read chunk_000000.tmp → Write to output              │
│  ├─ Read chunk_000001.tmp → Write to output              │
│  ├─ Read chunk_000002.tmp → Write to output              │
│  └─ Continue until all chunks merged                     │
└────────────────┬─────────────────────────────────────────┘

                 │ Verify integrity (if enabled)
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Final Verification                                        │
│  ├─ Calculate SHA-256 of assembled file                  │
│  ├─ Compare with sender's hash (if provided)             │
│  └─ Clean up temp directory                              │
└────────────────┬─────────────────────────────────────────┘

                 │ TransferController → COMPLETED
                 ▼
              SUCCESS
```

## Channel Selection Algorithm

```python
# Simplified pseudocode
def select_best_channel(available_channels, measurements):
    best_channel = None
    best_score = -∞
    
    for channel in available_channels:
        # Calculate multi-factor score
        speed = avg_speed_mbps[channel]
        error_rate = error_count[channel] / total_transfers[channel]
        latency = current_latency[channel]
        
        # Scoring function
        score = speed * 2.0          # Speed is primary factor
                - error_rate * 50    # Penalize errors heavily
                - latency * 0.1      # Minor latency penalty
        
        if score > best_score:
            best_score = score
            best_channel = channel
    
    return best_channel  # Returns "usb", "wifi", or None
```

## Error Handling Strategy

```
Transfer Operation
    ↓
Try to execute
    ├─ SUCCESS
    │   ├─ LogLevel: DEBUG
    │   └─ Mark chunk as transferred
    │
    └─ FAILURE (caught exception)
        ├─ Increment error count
        ├─ Log error (WARN level)
        ├─ Check retry count
        │   ├─ Retries available?
        │   │   ├─ YES → Re-queue with backoff
        │   │   │   └─ Sleep(RETRY_DELAY)
        │   │   │
        │   │   └─ NO → Mark as FAILED
        │   │       └─ Add to failed_chunks list
        │   │
        │   └─ Record in metrics for dashboard
        │
        └─ Continue with other chunks
```

## Memory Architecture

### For Send Operations

```
┌─────────────────────────────────────┐
│  GC (Python)                        │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ ChunkManager (State Map)     │   │
│  │ ├─ Dict[int, ChunkInfo]      │   │
│  │ │  └─ ~50 bytes per chunk    │   │
│  │ └─ For 1000 chunks: ~50 KB   │   │
│  │                              │   │
│  │ ┌──────────────────────────┐ │   │
│  │ │ Buffer Cache             │ │   │
│  │ │ ├─ 2x chunk_size          │   │
│  │ │ │  (for async overlap)   │ │   │
│  │ │ └─ 8 MB max              │ │   │
│  │ │                          │ │   │
│  │ │ Total: ~150 MB possible │ │   │
│  │ └──────────────────────────┘ │   │
│  └──────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### For Receive Operations

```
┌─────────────────────────────────────┐
│  Temp Directory (/tmp/...)          │ <- External storage
│  ├─ chunk_000000.tmp (4 MB)         │
│  ├─ chunk_000001.tmp (4 MB)         │
│  ├─ chunk_000002.tmp (4 MB)         │
│  └─ ...up to N chunks               │
│                                     │
│  Note: Chunks arrive out of order   │
│  but are stored on disk, not memory │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Memory (Minimal)                   │
│  ├─ ChunkAssembler state: ~1 MB     │
│  ├─ Channel buffers: ~1 MB          │
│  ├─ Metadata & tracking: ~1 MB      │
│  └─ Total: ~3-5 MB                  │
└─────────────────────────────────────┘
```

## Network Protocol

### Chunk Transfer Protocol

```
Communication Pattern:
    PC/Client          Android Device
         │                  │
         │──── CONNECT ───→ │
         │←─── ACK ────────│
         │                  │
         │─ CHUNK 0 (HD) ──→│
         │─ CHUNK 0 (DATA) →│
         │←── ACK ──────────│
         │                  │
         │─ CHUNK 1 (HD) ──→│
         │─ CHUNK 1 (DATA) →│
         │←── ACK ──────────│
         │                  │
         │──── DONE ──────→ │
         │←─ VERIFY/Done ──│
         │                  │


Header Format (8 bytes):
    ┌─────────────┬──────────────┐
    │ Chunk ID    │ Data Size    │
    │ (4 bytes)   │ (4 bytes)    │
    └─────────────┴──────────────┘
    
    Example:
    00 00 00 00 = Chunk 0
    00 00 40 00 = 16384 bytes (16KB)
    
Data Format (variable):
    ┌──────────────────────────┐
    │ Raw chunk data           │
    │ (4MB default)            │
    │ (size from header)       │
    └──────────────────────────┘
```

## Concurrency Model

### Async Pattern

```python
# Multiple operations happen concurrently
async def transfer_loop():
    tasks = [
        channel_a.send_chunk(chunk_0),  # Task 1
        channel_b.send_chunk(chunk_1),  # Task 2
        measure_speed_a(),              # Task 3
        measure_speed_b(),              # Task 4
    ]
    results = await asyncio.gather(*tasks)
    
# Benefits:
# - Single thread, non-blocking
# - No thread synchronization needed
# - Network waits don't block other transfers
```

## Scalability Considerations

### Chunk Size Selection

| Use Case | Chunk Size | Rationale |
|----------|-----------|-----------|
| LAN WiFi | 4-8 MB | Balance latency & throughput |
| Internet WiFi | 1-2 MB | Reduce timeout risk |
| USB 2.0 | 4 MB | Adequate for ~60 Mbps |
| USB 3.0 | 8-16 MB | Utilize higher bandwidth |
| Many small files | 512 KB | Quick transfers, low memory |

### Concurrent Transfers

```
Default: 2 chunks per channel simultaneously

USB:  ├─ Chunk A (sending)
      └─ Chunk B (queued)

WiFi: ├─ Chunk C (sending)
      └─ Chunk D (queued)

This limits memory usage while maintaining throughput.
```

## Implementation Details

### Type System Flow

```
Input → Pydantic Model → Internal Processing → Output
(JSON)    (Runtime          (Business         (Binary/JSON)
         Validated)         Logic)

Example:
{"transfer_id": "tx_123"} 
    ↓ ProgressiveUpdate.__init__()
    ↓ Fields validated
    ↓ Types coerced
    ↓ Ready for use
```

## Future: Rust Architecture

The Rust version will maintain identical architecture with native performance:

```rust
// Type-safe, zero-copy version
pub struct Transfer {
    controller: Arc<TransferController>,
    channels: Vec<Box<dyn Transport>>,
    scheduler: MultiChannelScheduler,
}

// Full async/await with tokio
#[tokio::main]
async fn main() {
    let transfer = Transfer::new();
    transfer.send().await?;
}
```

## Deployment Architecture

```
┌─────────────────────────────────────┐
│        User's PC                    │
│  ┌───────────────────────────────┐  │
│  │ HybridLink-Core Engine        │  │
│  │  ├─ USB:  ADB Forwarding      │  │
│  │  └─ WiFi: Listening on 9001   │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
          ↓ (USB) ↓ (WiFi)
┌─────────────────────────────────────┐
│        Android Device               │
│  ┌───────────────────────────────┐  │
│  │ HybridLink App                │  │
│  │  ├─ ADB: 127.0.0.1:9000       │  │
│  │  └─ WiFi: Listen on 9001      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Summary

HybridLink-Core's architecture provides:

1. **Modularity**: Each component is independently testable
2. **Scalability**: Handles GB+ files with minimal memory overhead
3. **Reliability**: Multiple redundant paths and verification
4. **Performance**: Concurrent transfers maximizing bandwidth
5. **Portability**: Language-agnostic design ready for Rust
6. **Maintainability**: Clear separation of concerns and type safety
