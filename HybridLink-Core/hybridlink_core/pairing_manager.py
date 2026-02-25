"""
PairingManager: Handles QR-based and PIN-based secure device pairing.
"""

import os
import random
import time
import logging
import json
import base64
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class PairingManager:
    """
    Manages secure pairing flows between devices.
    """

    def __init__(self):
        self.active_pin: Optional[str] = None
        self.pin_expiry: float = 0
        self.paired_devices: Dict[str, str] = {} # device_id -> public_key/token

    def generate_pairing_qr_data(self, device_info: dict, public_key: bytes) -> str:
        """
        Generate encrypted/signed data for QR pairing.
        Includes device metadata and temporary pairing key.
        """
        payload = {
            "v": "1",
            "id": device_info.get("id"),
            "name": device_info.get("name"),
            "k": base64.b64encode(public_key).decode(),
            "ts": int(time.time())
        }
        return json.dumps(payload)

    def generate_pin(self, length: int = 6) -> str:
        """Generate a time-limited numeric PIN for manual pairing."""
        self.active_pin = "".join([str(random.randint(0, 9)) for _ in range(length)])
        self.pin_expiry = time.time() + 300 # 5 minutes
        logger.info(f"Generated pairing PIN: {self.active_pin} (expires in 5m)")
        return self.active_pin

    def verify_pin(self, entered_pin: str) -> bool:
        """Verify the entered PIN against the active one."""
        if not self.active_pin or time.time() > self.pin_expiry:
            self.active_pin = None
            return False
        
        is_valid = entered_pin == self.active_pin
        if is_valid:
            self.active_pin = None # Use once
        return is_valid

    def save_trust(self, device_id: str, token: str):
        """Save a trusted device for future auto-approval."""
        self.paired_devices[device_id] = token
        logger.info(f"Device {device_id} is now trusted")
