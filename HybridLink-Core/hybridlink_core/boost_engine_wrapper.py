"""
BoostEngineWrapper: Bridge to the high-performance HybridFileXfer Java JAR.
"""

import subprocess
import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class BoostEngineWrapper:
    """Manages the lifecycle of the Java-based Boost Engine."""
    
    def __init__(self, jar_path: Optional[Path] = None, adb_path: Optional[Path] = None):
        if jar_path:
            self.jar_path = jar_path
        else:
            # Look in the package directory
            self.jar_path = Path(__file__).parent / "boost_engine" / "boost_engine.jar"
            
        if adb_path:
            self.adb_path = adb_path
        else:
            self.adb_path = Path(__file__).parent / "boost_engine" / "adb.exe"

    def is_java_available(self) -> bool:
        """Check if Java is installed and in PATH."""
        try:
            subprocess.run(["java", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def start_boost_transfer(self, mode: str, address: str, local_dir: str, device_id: Optional[str] = None):
        """
        Start a boosted transfer using the Java engine.
        
        Args:
            mode: 'send' or 'receive' (Note: the JAR uses its own CLI flags)
            address: 'adb' or IP address
            local_dir: Directory for the transfer
            device_id: Optional ADB device serial
        """
        if not self.is_java_available():
            logger.error("Java is not installed. Boost Mode requires Java JRE.")
            return None

        cmd = [
            "java",
            "-jar", str(self.jar_path),
            "-c", address,
            "-d", local_dir
        ]
        
        if device_id:
            cmd.extend(["-s", device_id])

        logger.info(f"Starting Boost Engine: {' '.join(cmd)}")
        
        # Start the process
        # On Windows, we might want to start it in a new window or attached
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        return process

    def setup_adb_boost(self, local_port: int, remote_port: int, device_serial: Optional[str] = None):
        """Setup ADB forward using the bundled ADB for Boost Mode."""
        cmd = [str(self.adb_path)]
        if device_serial:
            cmd.extend(["-s", device_serial])
        cmd.extend(["forward", f"tcp:{local_port}", f"tcp:{remote_port}"])
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB forward failed: {e.stderr.decode()}")
            return False
