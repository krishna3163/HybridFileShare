"""
Configuration and constants for HybridLink-Core.
"""

import os
from pathlib import Path
from enum import Enum

# Default chunk size: 4MB
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB

# USB (ADB TCP forwarding) defaults
USB_DEFAULT_HOST = "localhost"
USB_DEFAULT_PORT = 9000

# WiFi transport defaults
WIFI_DEFAULT_PORT = 9001
WIFI_TIMEOUT = 30.0

# Transfer timeouts
CHANNEL_TIMEOUT = 60.0
CHUNK_SEND_TIMEOUT = 120.0
HANDSHAKE_TIMEOUT = 10.0

# Retry policy
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# Progress reporting
PROGRESS_UPDATE_INTERVAL = 0.5  # seconds

# Temporary files
TEMP_DIR_SUFFIX = ".hybridlink_tmp"
METADATA_FILE = "transfer.metadata"
CHECKPOINT_EXTENSION = ".checkpoint"

# Channel throughput sampling
SPEED_SAMPLE_INTERVAL = 2.0
SPEED_SAMPLE_SIZE = 5


class TransferMode(str, Enum):
    """Transfer modes: SEND or RECEIVE."""

    SEND = "send"
    RECEIVE = "receive"


class ChannelType(str, Enum):
    """Available transport channels."""

    USB = "usb"
    WIFI = "wifi"


class TransferState(str, Enum):
    """Transfer state machine states."""

    IDLE = "idle"
    PREPARING = "preparing"
    TRANSFERRING = "transferring"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RESUMING = "resuming"


# Get platform-specific paths
def get_config_dir() -> Path:
    """Get platform-specific config directory."""
    if os.name == "nt":  # Windows
        config_dir = Path.home() / "AppData" / "Local" / "HybridLink"
    elif os.name == "posix":
        if os.uname().sysname == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "HybridLink"
        else:  # Linux and others
            config_dir = Path.home() / ".config" / "hybridlink"
    else:
        config_dir = Path.home() / ".hybridlink"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
