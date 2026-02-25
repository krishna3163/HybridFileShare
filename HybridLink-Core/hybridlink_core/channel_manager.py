"""
ChannelManager: Manages USB and WiFi channels, detects availability, and measures throughput.
"""

import logging
import asyncio
import time
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

from hybridlink_core.transport import TransportPlugin
from hybridlink_core.discovery_manager import DiscoveryManager, PeerDevice
from hybridlink_core.models import ChannelStats
from hybridlink_core.config import ChannelType, SPEED_SAMPLE_INTERVAL, SPEED_SAMPLE_SIZE

logger = logging.getLogger(__name__)


@dataclass
class ChannelMetrics:
    """Metrics for a channel."""

    channel_type: str
    available: bool = False
    bytes_transferred: int = 0
    speed_history: List[float] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[str] = None
    last_activity: float = 0.0

    @property
    def average_speed_mbps(self) -> float:
        """Get average speed from recent samples."""
        if not self.speed_history:
            return 0.0
        return sum(self.speed_history) / len(self.speed_history)

    @property
    def current_speed_mbps(self) -> float:
        """Get most recent speed measurement."""
        return self.speed_history[-1] if self.speed_history else 0.0


class ChannelManager:
    """
    Advanced ChannelManager with Mesh and Plugin support.
    """

    def __init__(self, device_id: str, device_name: str):
        self.channels: Dict[str, TransportPlugin] = {}
        self.peers: Dict[str, Dict[str, Any]] = {}
        self.metrics: Dict[str, ChannelMetrics] = {}
        self._speed_update_tasks: Dict[str, asyncio.Task] = {}
        self.discovery = DiscoveryManager(device_id, device_name)

    async def start_discovery(self):
        """Start both scanning and broadcasting."""
        await asyncio.gather(
            self.discovery.start_broadcasting(),
            self.discovery.start_scanning()
        )

    def register_transport(self, plugin: TransportPlugin):
        """Register a transport plugin (USB, WiFi, WebRTC, Relay)."""
        self.channels[plugin.name] = plugin
        self.metrics[plugin.name] = ChannelMetrics(channel_type=plugin.name)
        logger.info(f"Plugin registered: {plugin.name}")

    async def negotiate_peer_capabilities(self, peer_id: str) -> dict:
        """
        Exchange capability metadata with a paired peer.
        Identifies if the peer is a 'Browser Mode' or 'App Mode' node.
        """
        peer = self.discovery.discovered_peers.get(peer_id)
        if not peer:
            return {"mode": "unknown", "transports": []}
            
        capabilities = peer.capabilities or {}
        is_browser = peer.is_browser_mode
        
        negotiated = {
            "mode": "browser" if is_browser else "installed",
            "transports": peer.available_transports,
            "can_multipath": capabilities.get("multipath", False),
            "preferred_transport": "wifi" if not is_browser else "webrtc"
        }
        
        logger.info(f"Negotiated capabilities for {peer.name}: {negotiated['mode']} mode")
        return negotiated

    async def discover_mesh_peers(self):
        """Update mesh peer discovery with active scanning results."""
        peers = self.discovery.get_peers()
        for p in peers:
            self.peers[p["device_id"]] = p
        
        return self.peers

    async def connect_channel(self, channel_type: str) -> bool:
        """
        Connect a specific channel.
        
        Args:
            channel_type: Type of channel to connect
            
        Returns:
            True if connection successful
        """
        if channel_type not in self.channels:
            logger.warning(f"Channel not registered: {channel_type}")
            return False

        try:
            transport = self.channels[channel_type]
            connected = await transport.connect()

            if connected:
                self.metrics[channel_type].available = True
                self.metrics[channel_type].last_activity = time.time()

                # Start speed monitoring for this channel
                if channel_type not in self._speed_update_tasks:
                    task = asyncio.create_task(self._monitor_speed(channel_type))
                    self._speed_update_tasks[channel_type] = task

                logger.info(f"Channel connected: {channel_type}")
            else:
                self.metrics[channel_type].available = False
                logger.warning(f"Failed to connect channel: {channel_type}")

            return connected

        except Exception as e:
            logger.error(f"Error connecting channel {channel_type}: {e}")
            self.metrics[channel_type].available = False
            return False

    async def disconnect_channel(self, channel_type: str) -> None:
        """
        Disconnect a specific channel.
        
        Args:
            channel_type: Type of channel to disconnect
        """
        if channel_type not in self.channels:
            return

        try:
            # Cancel speed monitoring task
            if channel_type in self._speed_update_tasks:
                self._speed_update_tasks[channel_type].cancel()
                try:
                    await self._speed_update_tasks[channel_type]
                except asyncio.CancelledError:
                    pass
                del self._speed_update_tasks[channel_type]

            # Disconnect transport
            transport = self.channels[channel_type]
            await transport.disconnect()
            self.metrics[channel_type].available = False
            logger.info(f"Channel disconnected: {channel_type}")

        except Exception as e:
            logger.error(f"Error disconnecting channel {channel_type}: {e}")

    async def disconnect_all(self) -> None:
        """Disconnect all channels."""
        for channel_type in list(self.channels.keys()):
            await self.disconnect_channel(channel_type)

    async def is_channel_available(self, channel_type: str) -> bool:
        """
        Check if a channel is available and connected.
        
        Args:
            channel_type: Type of channel
            
        Returns:
            True if channel is available
        """
        if channel_type not in self.channels:
            return False

        try:
            transport = self.channels[channel_type]
            is_connected = await transport.is_connected()
            self.metrics[channel_type].available = is_connected
            return is_connected
        except Exception as e:
            logger.debug(f"Error checking channel {channel_type}: {e}")
            self.metrics[channel_type].available = False
            return False

    async def get_available_channels(self) -> List[str]:
        """
        Get list of available channels.
        
        Returns:
            List of available channel types
        """
        available = []
        for channel_type in self.channels:
            if await self.is_channel_available(channel_type):
                available.append(channel_type)
        return available

    def record_transfer(
        self, channel_type: str, bytes_transferred: int, error: Optional[str] = None
    ) -> None:
        """
        Record a transfer event on a channel.
        
        Args:
            channel_type: Type of channel
            bytes_transferred: Number of bytes transferred
            error: Optional error message
        """
        if channel_type not in self.metrics:
            return

        metrics = self.metrics[channel_type]
        metrics.bytes_transferred += bytes_transferred
        metrics.last_activity = time.time()

        if error:
            metrics.error_count += 1
            metrics.last_error = error
            logger.debug(f"Channel {channel_type} error: {error}")

    async def _monitor_speed(self, channel_type: str) -> None:
        """
        Continuously monitor and measure channel speed.
        
        Args:
            channel_type: Type of channel to monitor
        """
        try:
            while True:
                await asyncio.sleep(SPEED_SAMPLE_INTERVAL)

                if not await self.is_channel_available(channel_type):
                    continue

                try:
                    transport = self.channels[channel_type]
                    speed = await transport.measure_speed()

                    metrics = self.metrics[channel_type]
                    metrics.speed_history.append(speed)

                    # Keep only recent samples
                    if len(metrics.speed_history) > SPEED_SAMPLE_SIZE:
                        metrics.speed_history.pop(0)

                    logger.debug(
                        f"{channel_type} speed: {speed:.2f} Mbps "
                        f"(avg: {metrics.average_speed_mbps:.2f} Mbps)"
                    )

                except Exception as e:
                    logger.debug(f"Speed measurement error on {channel_type}: {e}")

        except asyncio.CancelledError:
            logger.debug(f"Speed monitoring cancelled for {channel_type}")
        except Exception as e:
            logger.error(f"Speed monitoring error for {channel_type}: {e}")

    def get_channel_stats(self, channel_type: str) -> Optional[ChannelStats]:
        """
        Get statistics for a channel.
        
        Args:
            channel_type: Type of channel
            
        Returns:
            ChannelStats if available, None otherwise
        """
        if channel_type not in self.metrics:
            return None

        metrics = self.metrics[channel_type]
        return ChannelStats(
            channel_type=channel_type,
            available=metrics.available,
            bytes_transferred=metrics.bytes_transferred,
            transfer_speed_mbps=metrics.average_speed_mbps,
            last_activity=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metrics.last_activity))
            if metrics.last_activity
            else None,
            error_count=metrics.error_count,
        )

    def get_all_stats(self) -> Dict[str, ChannelStats]:
        """Get statistics for all channels."""
        return {
            channel_type: self.get_channel_stats(channel_type)
            for channel_type in self.channels
        }

    def get_fastest_channel(self) -> Optional[str]:
        """
        Get the fastest available channel based on recent measurements.
        
        Returns:
            Channel type of fastest channel, or None if no channels available
        """
        available_channels = []

        for channel_type in self.channels:
            if self.metrics[channel_type].available:
                speed = self.metrics[channel_type].current_speed_mbps
                available_channels.append((channel_type, speed))

        if not available_channels:
            return None

        # Sort by speed (descending) and return fastest
        available_channels.sort(key=lambda x: x[1], reverse=True)
        return available_channels[0][0]

    def reset_stats(self) -> None:
        """Reset all channel statistics."""
        for metrics in self.metrics.values():
            metrics.bytes_transferred = 0
            metrics.speed_history = []
            metrics.error_count = 0
            metrics.last_error = None
        logger.info("Channel statistics reset")

    def get_summary(self) -> dict:
        """Get summary of all channels."""
        summary = {
            "total_channels": len(self.channels),
            "available_channels": sum(1 for m in self.metrics.values() if m.available),
            "channels": {},
        }

        for channel_type, metrics in self.metrics.items():
            summary["channels"][channel_type] = {
                "available": metrics.available,
                "bytes_transferred": metrics.bytes_transferred,
                "current_speed_mbps": metrics.current_speed_mbps,
                "average_speed_mbps": metrics.average_speed_mbps,
                "error_count": metrics.error_count,
            }

        return summary
