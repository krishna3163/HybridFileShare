"""
Windows Connection Manager: Dual-channel USB+WiFi connection orchestration.

Manages:
- USB connection via ADB port forwarding
- WiFi connection via SSH or TCP socket
- Connection health monitoring
- Automatic failover
- Channel speed measurement
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field
from datetime import datetime
import socket

from paramiko.ssh_exception import SSHException

logger = logging.getLogger(__name__)


@dataclass
class ChannelHealth:
    """Health metrics for a single channel."""
    channel_name: str
    is_available: bool = False
    last_check_time: float = 0.0
    latency_ms: float = 0.0
    speed_mbps: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    bytes_transferred: int = 0
    packets_lost: float = 0.0  # Percentage

    def is_healthy(self) -> bool:
        """Check if channel is healthy."""
        return self.is_available and self.error_count < 5

    def get_quality_score(self) -> float:
        """
        Calculate channel quality score (0.0 to 1.0).
        
        Takes into account: availability, latency, error rate
        """
        if not self.is_available:
            return 0.0
        
        # Base score on availability
        score = 1.0
        
        # Reduce for high latency (> 100ms is bad)
        if self.latency_ms > 100:
            score *= 0.5
        elif self.latency_ms > 50:
            score *= 0.7
        
        # Reduce for errors
        error_rate = min(self.error_count / 10.0, 1.0)
        score *= (1.0 - error_rate * 0.5)
        
        return score


class DualChannelConnectionManager:
    """
    Manages USB + WiFi dual-channel connections with health monitoring.
    
    Features:
    - Simultaneous USB and WiFi connections
    - Per-channel health tracking
    - Automatic failover when channel degrades
    - Speed measurement for intelligent scheduling
    - Graceful connection teardown
    """

    def __init__(
        self,
        device_serial: str,
        wifi_host: str,
        wifi_port: int = 9001,
        usb_local_port: int = 9000,
        usb_remote_port: int = 9001,
    ):
        """
        Initialize dual-channel connection manager.
        
        Args:
            device_serial: Android device serial (for ADB)
            wifi_host: WiFi host IP address
            wifi_port: WiFi port
            usb_local_port: Local port for USB forwarding
            usb_remote_port: Remote port on device
        """
        self.device_serial = device_serial
        self.wifi_host = wifi_host
        self.wifi_port = wifi_port
        self.usb_local_port = usb_local_port
        self.usb_remote_port = usb_remote_port

        # Channel state
        self.channels: Dict[str, Dict] = {
            "usb": {"socket": None, "connected": False},
            "wifi": {"socket": None, "connected": False},
        }
        self.health = {
            "usb": ChannelHealth("USB (ADB)"),
            "wifi": ChannelHealth("WiFi"),
        }

        # Monitoring
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._health_check_interval = 2.0
        self._on_channel_status_changed: Optional[Callable] = None

    async def initialize_connections(self, adb_manager=None) -> bool:
        """
        Initialize USB and WiFi connections.
        
        Args:
            adb_manager: Optional AdbManager for USB setup
            
        Returns:
            True if at least one channel connects
        """
        logger.info("Initializing dual-channel connections...")
        
        # Start USB connection
        usb_ready = False
        if adb_manager:
            try:
                if adb_manager.forward_port(
                    self.device_serial,
                    self.usb_remote_port,
                    self.usb_local_port,
                ):
                    usb_ready = await self._test_usb_connection()
                    if usb_ready:
                        logger.info("✓ USB channel ready (ADB port forwarding)")
                        self.channels["usb"]["connected"] = True
                        self.health["usb"].is_available = True
            except Exception as e:
                logger.warning(f"USB setup failed: {e}")

        # Start WiFi connection
        wifi_ready = await self._test_wifi_connection()
        if wifi_ready:
            logger.info("✓ WiFi channel ready")
            self.channels["wifi"]["connected"] = True
            self.health["wifi"].is_available = True

        if not (usb_ready or wifi_ready):
            logger.error("Failed to establish any connection")
            return False

        # Start health monitoring
        self._health_monitor_task = asyncio.create_task(self._monitor_health())

        return True

    async def _test_usb_connection(self, timeout: float = 5.0) -> bool:
        """
        Test USB connection via ADB port forwarding.
        
        Args:
            timeout: Connection timeout
            
        Returns:
            True if connection successful
        """
        try:
            sock = socket.create_connection(
                ("127.0.0.1", self.usb_local_port),
                timeout=timeout,
            )
            
            # Send and receive test data
            test_msg = b"PING"
            sock.send(test_msg)
            response = sock.recv(1024)
            
            self.channels["usb"]["socket"] = sock
            return True
        except Exception as e:
            logger.debug(f"USB connection test failed: {e}")
            return False

    async def _test_wifi_connection(self, timeout: float = 5.0) -> bool:
        """
        Test WiFi connection.
        
        Args:
            timeout: Connection timeout
            
        Returns:
            True if connection successful
        """
        try:
            sock = socket.create_connection(
                (self.wifi_host, self.wifi_port),
                timeout=timeout,
            )
            
            # Send and receive test data
            test_msg = b"PING"
            sock.send(test_msg)
            response = sock.recv(1024)
            
            self.channels["wifi"]["socket"] = sock
            return True
        except Exception as e:
            logger.debug(f"WiFi connection test failed: {e}")
            return False

    async def _monitor_health(self) -> None:
        """
        Continuously monitor channel health.
        
        Measures: latency, errors, availability
        """
        while not self._shutdown_event.is_set():
            try:
                # Check USB health
                if self.channels["usb"]["connected"]:
                    await self._check_channel_health("usb")
                
                # Check WiFi health
                if self.channels["wifi"]["connected"]:
                    await self._check_channel_health("wifi")
                
                # Notify if status changed
                if self._on_channel_status_changed:
                    await self._on_channel_status_changed(self.get_channel_status())
                
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                logger.debug(f"Health check error: {e}")

    async def _check_channel_health(self, channel_name: str) -> None:
        """
        Check health of a specific channel.
        
        Args:
            channel_name: "usb" or "wifi"
        """
        try:
            sock = self.channels[channel_name].get("socket")
            if not sock:
                self.health[channel_name].is_available = False
                return

            # Measure latency
            start_time = time.time()
            sock.send(b"PING")
            sock.recv(1024)
            latency = (time.time() - start_time) * 1000  # ms

            self.health[channel_name].latency_ms = latency
            self.health[channel_name].is_available = True
            self.health[channel_name].error_count = max(0, self.health[channel_name].error_count - 1)
        except Exception as e:
            logger.debug(f"Health check failed for {channel_name}: {e}")
            self.health[channel_name].error_count += 1
            self.health[channel_name].last_error = str(e)
            
            if self.health[channel_name].error_count >= 3:
                self.health[channel_name].is_available = False
                logger.warning(f"{channel_name} channel degraded after {self.health[channel_name].error_count} errors")

    async def measure_channel_speed(self, channel_name: str, test_size: int = 1024 * 1024) -> float:
        """
        Measure transfer speed for a channel.
        
        Args:
            channel_name: "usb" or "wifi"
            test_size: Size of test data in bytes
            
        Returns:
            Speed in Mbps
        """
        try:
            sock = self.channels[channel_name].get("socket")
            if not sock:
                return 0.0

            test_data = b"X" * test_size
            start_time = time.time()
            sock.send(test_data)
            elapsed = time.time() - start_time
            
            speed_mbps = (test_size * 8 / elapsed) / (1024 * 1024)
            self.health[channel_name].speed_mbps = speed_mbps
            return speed_mbps
        except Exception as e:
            logger.debug(f"Speed measurement failed for {channel_name}: {e}")
            return 0.0

    def get_channel_status(self) -> Dict:
        """Get status of all channels."""
        return {
            "usb": {
                "available": self.health["usb"].is_available,
                "healthy": self.health["usb"].is_healthy(),
                "latency_ms": self.health["usb"].latency_ms,
                "speed_mbps": self.health["usb"].speed_mbps,
                "quality_score": self.health["usb"].get_quality_score(),
                "error_count": self.health["usb"].error_count,
            },
            "wifi": {
                "available": self.health["wifi"].is_available,
                "healthy": self.health["wifi"].is_healthy(),
                "latency_ms": self.health["wifi"].latency_ms,
                "speed_mbps": self.health["wifi"].speed_mbps,
                "quality_score": self.health["wifi"].get_quality_score(),
                "error_count": self.health["wifi"].error_count,
            },
        }

    def get_best_channel(self) -> Optional[str]:
        """
        Get the best available channel based on quality.
        
        Returns:
            "usb" or "wifi" or None
        """
        usb_score = self.health["usb"].get_quality_score()
        wifi_score = self.health["wifi"].get_quality_score()
        
        if usb_score > wifi_score and usb_score > 0:
            return "usb"
        elif wifi_score > 0:
            return "wifi"
        elif usb_score > 0:
            return "usb"
        
        return None

    def has_any_channel(self) -> bool:
        """Check if at least one channel is available."""
        return self.health["usb"].is_available or self.health["wifi"].is_available

    async def teardown(self) -> None:
        """Gracefully close all connections."""
        logger.info("Tearing down connections...")
        self._shutdown_event.set()

        if self._health_monitor_task:
            try:
                await asyncio.wait_for(self._health_monitor_task, timeout=2.0)
            except asyncio.TimeoutError:
                self._health_monitor_task.cancel()

        for channel_name, channel_data in self.channels.items():
            sock = channel_data.get("socket")
            if sock:
                try:
                    sock.close()
                    logger.info(f"Closed {channel_name} connection")
                except Exception as e:
                    logger.debug(f"Error closing {channel_name}: {e}")

    def set_on_status_changed(self, callback: Callable) -> None:
        """
        Set callback for when channel status changes.
        
        Args:
            callback: Async callable(status_dict)
        """
        self._on_channel_status_changed = callback


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def test():
        manager = DualChannelConnectionManager(
            device_serial="12345",
            wifi_host="192.168.1.100",
        )
        
        try:
            connected = await manager.initialize_connections()
            if connected:
                print("Connected!")
                print("\nChannel Status:")
                print(manager.get_channel_status())
                print(f"\nBest channel: {manager.get_best_channel()}")
                
                await asyncio.sleep(5)
            else:
                print("Failed to connect")
        finally:
            await manager.teardown()

    asyncio.run(test())
