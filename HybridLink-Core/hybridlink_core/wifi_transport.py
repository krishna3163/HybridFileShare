"""
WiFi transport using native TCP sockets.
"""

import logging
import asyncio
import socket
import time
from typing import Optional, Tuple

from hybridlink_core.usb_transport import TransportBase, TransportConfig
from hybridlink_core.config import WIFI_DEFAULT_PORT, WIFI_TIMEOUT

logger = logging.getLogger(__name__)


class WifiTransport(TransportBase):
    """
    WiFi transport using native TCP sockets.
    
    Connects to Android device's WiFi server on a configurable port.
    """

    def __init__(
        self,
        host: str,
        port: int = WIFI_DEFAULT_PORT,
        config: Optional[TransportConfig] = None,
    ):
        """
        Initialize WiFi transport.
        
        Args:
            host: Android device IP address or hostname
            port: Port number (default: 9001)
            config: Transport configuration
        """
        self.host = host
        self.port = port
        self.config = config or TransportConfig(timeout=WIFI_TIMEOUT)
        self.socket: Optional[socket.socket] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish WiFi connection to Android device.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create a non-blocking socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setblocking(False)

            # Attempt connection with timeout
            loop = asyncio.get_event_loop()
            try:
                await asyncio.wait_for(
                    loop.sock_connect(self.socket, (self.host, self.port)),
                    timeout=self.config.timeout,
                )
            except (socket.error, OSError) as e:
                if e.errno != 115 and e.errno != 111:  # Not "in progress" or "connection refused"
                    raise

            self._connected = True
            logger.info(f"Connected to WiFi transport at {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect WiFi transport: {e}")
            self._connected = False
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
                self.socket = None
            return False

    async def disconnect(self) -> None:
        """Close WiFi connection."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.warning(f"Error closing WiFi socket: {e}")
            self.socket = None
        self._connected = False
        logger.info("WiFi transport disconnected")

    async def is_connected(self) -> bool:
        """Check if WiFi connection is active."""
        if not self.socket or not self._connected:
            return False

        try:
            # Non-blocking peek to check connection
            self.socket.setblocking(False)
            data = self.socket.recv(0, socket.MSG_PEEK)
            return True
        except (BlockingIOError, socket.timeout):
            return True  # Still connected, just no data
        except Exception:
            self._connected = False
            return False

    async def send_chunk(self, chunk_data: bytes, chunk_id: int) -> Tuple[bool, int]:
        """
        Send a chunk over WiFi transport.
        
        Args:
            chunk_data: The raw chunk data
            chunk_id: The chunk ID
            
        Returns:
            Tuple of (success, bytes_sent)
        """
        if not self.socket or not self._connected:
            return False, 0

        try:
            loop = asyncio.get_event_loop()

            # Send header: chunk_id (4 bytes) + size (4 bytes)
            header = chunk_id.to_bytes(4, "big") + len(chunk_data).to_bytes(4, "big")

            # Send header
            await asyncio.wait_for(
                loop.sock_sendall(self.socket, header), timeout=self.config.timeout
            )

            # Send data
            await asyncio.wait_for(
                loop.sock_sendall(self.socket, chunk_data), timeout=self.config.timeout
            )

            logger.debug(f"WiFi: Sent chunk {chunk_id} ({len(chunk_data)} bytes)")
            return True, len(chunk_data)

        except asyncio.TimeoutError:
            logger.error(f"WiFi: Timeout sending chunk {chunk_id}")
            return False, 0
        except Exception as e:
            logger.error(f"WiFi: Error sending chunk {chunk_id}: {e}")
            self._connected = False
            return False, 0

    async def receive_chunk(self) -> Optional[bytes]:
        """
        Receive a chunk over WiFi transport.
        
        Returns:
            Chunk data if successful, None otherwise
        """
        if not self.socket or not self._connected:
            return None

        try:
            loop = asyncio.get_event_loop()

            # Receive header (8 bytes: chunk_id + size)
            header = await asyncio.wait_for(
                loop.sock_recv(self.socket, 8), timeout=self.config.timeout
            )

            if len(header) < 8:
                logger.error("WiFi: Invalid header received")
                return None

            chunk_id = int.from_bytes(header[:4], "big")
            size = int.from_bytes(header[4:8], "big")

            if size > 100 * 1024 * 1024:  # Sanity check: max 100MB chunk
                logger.error(f"WiFi: Chunk size too large: {size}")
                return None

            # Receive data in chunks
            data = b""
            remaining = size

            while remaining > 0:
                to_read = min(self.config.buffer_size, remaining)
                chunk = await asyncio.wait_for(
                    loop.sock_recv(self.socket, to_read), timeout=self.config.timeout
                )

                if not chunk:
                    logger.error(f"WiFi: Connection closed while receiving chunk {chunk_id}")
                    return None

                data += chunk
                remaining -= len(chunk)

            logger.debug(f"WiFi: Received chunk {chunk_id} ({len(data)} bytes)")
            return data

        except asyncio.TimeoutError:
            logger.error("WiFi: Timeout receiving chunk")
            return None
        except Exception as e:
            logger.error(f"WiFi: Error receiving chunk: {e}")
            self._connected = False
            return None

    async def measure_speed(self) -> float:
        """
        Measure WiFi transport speed with a small test transfer.
        
        Returns:
            Speed in Mbps
        """
        if not self.socket or not self._connected:
            return 0.0

        test_size = 1024 * 1024  # 1MB test
        test_data = b"X" * test_size

        try:
            loop = asyncio.get_event_loop()
            start = time.time()

            # Send header
            header = (0).to_bytes(4, "big") + test_size.to_bytes(4, "big")
            await asyncio.wait_for(
                loop.sock_sendall(self.socket, header), timeout=self.config.timeout
            )

            # Send test data
            await asyncio.wait_for(
                loop.sock_sendall(self.socket, test_data), timeout=self.config.timeout
            )

            elapsed = time.time() - start
            speed_mbps = (test_size * 8) / (elapsed * 1_000_000)  # Convert to Mbps
            logger.debug(f"WiFi speed: {speed_mbps:.2f} Mbps")
            return speed_mbps

        except Exception as e:
            logger.error(f"WiFi: Speed measurement failed: {e}")
            return 0.0
