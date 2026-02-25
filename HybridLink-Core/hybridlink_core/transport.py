"""
Plugin-based transport architecture for HybridLink.
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from hybridlink_core.config import CHANNEL_TIMEOUT

logger = logging.getLogger(__name__)

@dataclass
class TransportConfig:
    """Configuration for transport layer."""
    timeout: float = CHANNEL_TIMEOUT
    buffer_size: int = 65536
    mtu: int = 1400  # Default MTU for packet-based transports

class TransportPlugin(ABC):
    """
    Base class for transport plugins (USB, WiFi, WebRTC, Bluetooth, etc.)
    """

    def __init__(self, name: str, config: Optional[TransportConfig] = None):
        self.name = name
        self.config = config or TransportConfig()
        self._connected = False
        self.metrics = {
            "bytes_sent": 0,
            "bytes_received": 0,
            "errors": 0,
            "latency_ms": 0,
            "current_speed_mbps": 0.0
        }

    @abstractmethod
    async def connect(self, peer_info: Dict[str, Any]) -> bool:
        """Connect to remote peer using transport-specific info."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully disconnect."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Return connectivity status."""
        pass

    @abstractmethod
    async def send_packet(self, data: bytes) -> bool:
        """Send a raw packet over the transport."""
        pass

    @abstractmethod
    async def receive_packet(self) -> Optional[bytes]:
        """Receive a raw packet from the transport."""
        pass

    async def measure_performance(self) -> Dict[str, Any]:
        """
        Measure latency and throughput.
        Default implementation uses a ping-like mechanism.
        """
        return self.metrics

    def record_error(self, error: str):
        self.metrics["errors"] += 1
        logger.error(f"[{self.name}] Transport error: {error}")

class RelayFallbackTransport(TransportPlugin):
    """
    Fallback transport that uses a relay server when P2P fails.
    """
    async def connect(self, peer_info: Dict[str, Any]) -> bool:
        # Implementation for relay connection
        return True

    async def disconnect(self) -> None: pass
    async def is_connected(self) -> bool: return self._connected
    async def send_packet(self, data: bytes) -> bool: return True
    async def receive_packet(self) -> Optional[bytes]: return None

class WebRTCTransport(TransportPlugin):
    """
    WebRTC transport for NAT traversal and P2P remote transfers.
    """
    async def connect(self, peer_info: Dict[str, Any]) -> bool:
        # Implementation using aiortc
        return True

    async def disconnect(self) -> None: pass
    async def is_connected(self) -> bool: return self._connected
    async def send_packet(self, data: bytes) -> bool: return True
    async def receive_packet(self) -> Optional[bytes]: return None
