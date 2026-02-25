"""
Windows Utilities: ADB detection, device enumeration, and Windows-specific operations.

Provides utilities for:
- Detecting ADB availability on Windows
- Enumerating connected Android devices via ADB
- Setting up ADB port forwarding
- Windows-specific path and subprocess handling
"""

import subprocess
import logging
import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AndroidDevice:
    """Represents a connected Android device."""
    serial: str
    name: str
    is_emulator: bool = False
    state: str = "device"  # "offline", "device", "unauthorized", etc.

    def __str__(self) -> str:
        device_type = "emulator" if self.is_emulator else "device"
        return f"{self.serial} ({self.name}) - {device_type} [{self.state}]"


class AdbManager:
    """
    Manages ADB operations on Windows.
    
    Features:
    - Auto-detect ADB location
    - List connected devices
    - Setup port forwarding
    - Execute ADB commands
    - Handle Windows-specific subprocess issues
    """

    def __init__(self, adb_path: Optional[str] = None):
        """
        Initialize ADB manager.
        
        Args:
            adb_path: Optional explicit path to adb executable.
                     If not provided, will search in common locations.
        """
        self.adb_path = adb_path
        self._validate_adb()

    def _validate_adb(self) -> None:
        """
        Validate ADB is available and executable.
        
        Raises:
            FileNotFoundError: If ADB cannot be found
        """
        if self.adb_path:
            if not Path(self.adb_path).exists():
                raise FileNotFoundError(f"ADB not found at: {self.adb_path}")
            logger.info(f"Using ADB from: {self.adb_path}")
            return

        # Try to find ADB in common Windows locations
        potential_paths = [
            shutil.which("adb"),  # In PATH
            Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe",
            Path("C:/Android/sdk/platform-tools/adb.exe"),
            Path("C:/Program Files/Android/Sdk/platform-tools/adb.exe"),
            Path("C:/Program Files (x86)/Android/Sdk/platform-tools/adb.exe"),
        ]

        for path in potential_paths:
            if path and isinstance(path, str):
                path = Path(path)
            if path and path.exists():
                self.adb_path = str(path)
                logger.info(f"Found ADB at: {self.adb_path}")
                return

        raise FileNotFoundError(
            "ADB not found. Install Android SDK or provide explicit path. "
            "See: https://developer.android.com/tools/releases/platform-tools"
        )

    def _run_adb_command(self, *args, check: bool = True) -> str:
        """
        Run an ADB command and return output.
        
        Args:
            *args: Command arguments (e.g., "devices", "shell", "cmd")
            check: Raise error if command fails
            
        Returns:
            Command output as string
            
        Raises:
            subprocess.CalledProcessError: If command fails and check=True
        """
        if not self.adb_path:
            raise RuntimeError("ADB not initialized")

        cmd = [self.adb_path] + list(args)
        
        try:
            # Use creationflags on Windows to avoid console window
            kwargs = {
                "capture_output": True,
                "text": True,
                "check": check,
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(cmd, **kwargs)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB command failed: {' '.join(cmd)}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise

    def get_adb_version(self) -> str:
        """Get ADB version."""
        try:
            return self._run_adb_command("version")
        except Exception as e:
            logger.error(f"Failed to get ADB version: {e}")
            return "unknown"

    def list_devices(self) -> List[AndroidDevice]:
        """
        List all connected Android devices.
        
        Returns:
            List of AndroidDevice objects
        """
        try:
            output = self._run_adb_command("devices", "-l")
            lines = output.split("\n")[1:]  # Skip header
            
            devices = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Parse: "emulator-5554 device usb:1-1 product:generic_x86 model:Android_SDK_built_for_x86"
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                serial = parts[0]
                state = parts[1]
                is_emulator = serial.startswith("emulator-")
                
                # Extract device name from model or product
                name = "Unknown"
                for part in parts[2:]:
                    if part.startswith("model:"):
                        name = part.split(":", 1)[1]
                        break
                    elif part.startswith("product:"):
                        name = part.split(":", 1)[1]
                
                devices.append(AndroidDevice(
                    serial=serial,
                    name=name,
                    is_emulator=is_emulator,
                    state=state,
                ))
            
            return devices
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []

    def forward_port(
        self,
        device_serial: str,
        remote_port: int,
        local_port: int = 9000,
    ) -> bool:
        """
        Setup ADB port forwarding for a device.
        
        Example: adb forward tcp:9000 tcp:9001 (forwards local 9000 to device 9001)
        
        Args:
            device_serial: Device serial number
            remote_port: Port on Android device
            local_port: Local port on PC
            
        Returns:
            True if successful
        """
        try:
            self._run_adb_command(
                "-s", device_serial,
                "forward",
                f"tcp:{local_port}",
                f"tcp:{remote_port}",
            )
            logger.info(f"Forwarded tcp:{local_port} -> {device_serial}:tcp:{remote_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to forward port: {e}")
            return False

    def remove_forward(
        self,
        device_serial: str,
        local_port: int = 9000,
    ) -> bool:
        """
        Remove ADB port forwarding.
        
        Args:
            device_serial: Device serial number
            local_port: Local port to remove
            
        Returns:
            True if successful
        """
        try:
            self._run_adb_command(
                "-s", device_serial,
                "forward",
                "--remove",
                f"tcp:{local_port}",
            )
            logger.info(f"Removed forward for tcp:{local_port}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove forward: {e}")
            return False

    def execute_shell_command(
        self,
        device_serial: str,
        command: str,
    ) -> str:
        """
        Execute a shell command on the device.
        
        Args:
            device_serial: Device serial number
            command: Shell command to execute
            
        Returns:
            Command output
        """
        try:
            return self._run_adb_command(
                "-s", device_serial,
                "shell",
                command,
            )
        except Exception as e:
            logger.error(f"Failed to execute shell command: {e}")
            return ""

    def is_device_authorized(self, device_serial: str) -> bool:
        """Check if device is authorized (not 'unauthorized')."""
        devices = self.list_devices()
        for device in devices:
            if device.serial == device_serial:
                return device.state != "unauthorized"
        return False


class DeviceDetector:
    """
    High-level device detection and connection verification.
    """

    def __init__(self):
        """Initialize device detector."""
        try:
            self.adb = AdbManager()
        except FileNotFoundError as e:
            self.adb = None
            logger.warning(f"ADB not available: {e}")

    def is_adb_available(self) -> bool:
        """Check if ADB is available."""
        return self.adb is not None

    def detect_connected_device(self) -> Optional[AndroidDevice]:
        """
        Detect a single connected Android device.
        
        Priority:
        1. Physical devices
        2. Emulators
        
        Returns:
            First available device or None
        """
        if not self.adb:
            return None

        devices = self.adb.list_devices()
        if not devices:
            return None

        # Prefer physical devices
        physical = [d for d in devices if not d.is_emulator and d.state == "device"]
        if physical:
            return physical[0]

        # Fall back to emulators
        authorized = [d for d in devices if d.state == "device"]
        if authorized:
            return authorized[0]

        # Even if unauthorized, return it for user reference
        return devices[0] if devices else None

    def check_wifi_reachability(self, host: str, port: int = 22, timeout: int = 2) -> bool:
        """
        Check if WiFi host is reachable (for SSH verification).
        
        Args:
            host: WiFi host IP or hostname
            port: Port to check (default 22 for SSH)
            timeout: Timeout in seconds
            
        Returns:
            True if reachable
        """
        import socket
        
        try:
            socket.create_connection((host, port), timeout=timeout)
            return True
        except (socket.timeout, OSError):
            return False

    def get_device_ip_via_adb(self, device_serial: str) -> Optional[str]:
        """
        Try to get device IP address via ADB shell.
        
        Args:
            device_serial: Device serial number
            
        Returns:
            IP address or None
        """
        if not self.adb:
            return None

        try:
            # Try to get IP from ifconfig or similar
            output = self.adb.execute_shell_command(
                device_serial,
                "ip addr show | grep 'inet ' | grep -v '127.0' | head -1 | awk '{print $2}' | cut -d'/' -f1"
            )
            if output:
                return output.strip()
            return None
        except Exception as e:
            logger.debug(f"Failed to get device IP: {e}")
            return None


# Windows-specific path utilities
def to_windows_path(path: str) -> str:
    """Convert path to Windows format."""
    return str(Path(path))


def to_forward_slash_path(path: str) -> str:
    """Convert path to forward slash format for cross-platform compatibility."""
    return str(Path(path)).replace("\\", "/")


def is_valid_file_path(path: str) -> bool:
    """Check if file path is valid."""
    try:
        Path(path).resolve()
        return True
    except (ValueError, OSError):
        return False


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f}PB"


# Example usage
if __name__ == "__main__":
    # Test ADB manager
    try:
        adb = AdbManager()
        print(f"ADB Version: {adb.get_adb_version()}")
        print("\nConnected Devices:")
        devices = adb.list_devices()
        for device in devices:
            print(f"  {device}")
    except Exception as e:
        print(f"Error: {e}")

    # Test device detector
    detector = DeviceDetector()
    if detector.is_adb_available():
        device = detector.detect_connected_device()
        if device:
            print(f"\nDetected Device: {device}")
        else:
            print("\nNo connected devices found")
    else:
        print("\nADB not available")
