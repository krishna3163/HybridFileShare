"""
DiscoveryManager: Handles mDNS, UDP broadcast, and Bluetooth LE advertisements for device discovery.
"""

import logging
import asyncio
import socket
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class PeerDevice:
    device_id: str
    name: str
    os_type: str
    ip_address: Optional[str] = None
    available_transports: List[str] = None
    trust_status: str = "untrusted" # untrusted, paired, trusted
    last_seen: float = 0.0

class DiscoveryManager:
    """
    Manages cross-platform device discovery.
    
    Features:
    - UDP Broadcast for LAN discovery
    - mDNS support (placeholder for zeroconf)
    - Metadata broadcasting
    """

    def __init__(self, device_id: str, device_name: str, port: int = 8080):
        self.device_id = device_id
        self.device_name = device_name
        self.port = port
        self.discovered_peers: Dict[str, PeerDevice] = {}
        self._is_broadcasting = False
        self._is_scanning = False

    async def start_broadcasting(self):
        """Broadcast presence via UDP on the local network."""
        self._is_broadcasting = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)

        message = {
            "type": "HYBRIDLINK_DISCOVERY",
            "device_id": self.device_id,
            "name": self.device_name,
            "os": "Windows", # Dynamically detect in production
            "transports": ["wifi", "usb", "bluetooth"],
            "port": self.port
        }
        
        data = json.dumps(message).encode()
        logger.info(f"Started discovery broadcast: {self.device_name} ({self.device_id})")

        while self._is_broadcasting:
            try:
                # Broadcast on common subnets or global broadcast
                sock.sendto(data, ('255.255.255.255', 8888))
                await asyncio.sleep(5) # Broadcast every 5 seconds
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                await asyncio.sleep(10)

    async def start_scanning(self):
        """Listen for UDP discovery broadcasts from other devices."""
        self._is_scanning = True
        loop = asyncio.get_event_loop()
        
        # Create server socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 8888))
        sock.setblocking(False)
        
        logger.info("Started scanning for nearby devices...")
        
        while self._is_scanning:
            try:
                data, addr = await loop.sock_recvfrom(sock, 1024)
                payload = json.loads(data.decode())
                
                if payload.get("type") == "HYBRIDLINK_DISCOVERY":
                    peer_id = payload["device_id"]
                    if peer_id == self.device_id: continue
                    
                    self.discovered_peers[peer_id] = PeerDevice(
                        device_id=peer_id,
                        name=payload["name"],
                        os_type=payload["os"],
                        ip_address=addr[0],
                        available_transports=payload["transports"],
                        last_seen=asyncio.get_event_loop().time()
                    )
                    logger.debug(f"Discovered peer: {payload['name']} at {addr[0]}")
            except Exception as e:
                if self._is_scanning:
                    logger.error(f"Scan error: {e}")
                await asyncio.sleep(1)

    def stop(self):
        self._is_broadcasting = False
        self._is_scanning = False

    def get_peers(self) -> List[Dict[str, Any]]:
        return [asdict(p) for p in self.discovered_peers.values()]
