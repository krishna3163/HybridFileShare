# HybridFileXfer Integration Architecture

This document details the architectural integration map of **HybridFileXfer (多轨快传)** features into the existing **HybridLink** ecosystem.

## 1. Core Multipath Queuing Engine

We are implementing a dual-queue chunk processing model similar to FastCopy.

*   **Sender**: File is divided into 1MB chunks and placed in a `SendQueue`. Multiple transport threads (USB, WiFi_5G, WiFi_2.4G) aggressively pull from this queue.
*   **Receiver**: Transports push received chunks into a `ReceiveQueue`. A dedicated `DiskWriter` thread monitors the queue and sequentially writes contiguous chunks to disk prioritizing mechanical/flash write performance.

### Migration from Single Channel to Dual Queue
`chunk_assembler.py` and `multichannel_scheduler.py` will be refactored to use standard Lock-free queues (or ThreadSafe `asyncio.Queue`) for continuous buffered operations.

## 2. ADB Port Forwarding Automation

Currently, ADB port forwarding (USB transport) expects external manual running of `adb forward tcp:9000 tcp:9000`. 
We are updating `hybridlink_core/usb_transport.py` and `windows_connection_manager.py` to auto-detect ADB devices, request USB debugging permissions, and automatically establish port forwarding for the USB channel, removing the need for manual `.bat` scripts.

## 3. Advanced Networking Interfaces

Android Mobile App (`app/`) is updated to strictly enumerate network interfaces during discovery:
- `wlan0` (2.4GHz WiFi)
- `wlan1` (5GHz WiFi / WiFi Direct)
- `usb0` (USB Tethering)
- `eth0` (Physical Ethernet via Dock)

When initiating a transfer, the Mobile Server spins up multiple listening sockets bound specifically to these interfaces. The PC Client (`windows_connection_manager.py`) connects to all of them.

## 4. Root / Shizuku Directory Access

For Android 11+ App Data access (e.g. `Android/data`), HybridLink Android App will implement **Shizuku** IPC.
This allows high-performance reads directly from root-protected folders without copying data to scoped storage first.

## 5. UI Overhaul 

The Dashboards (Web & Windows) are updated to display:
- Detailed multi-channel diagnostic cards with live dual-speed meters (e.g., WiFi: 110MB/s, USB: 40MB/s).
- Visual connection map prioritizing direct IP and ADB bindings.
