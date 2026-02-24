"""
HybridLink-Core: Cross-platform multipath transfer engine for USB and WiFi.
"""

__version__ = "0.1.0"
__author__ = "HybridLink Team"

from hybridlink_core.models import (
    ChunkInfo,
    TransferMetadata,
    ChannelStats,
    TransferConfig,
)
from hybridlink_core.chunk_manager import ChunkManager
from hybridlink_core.channel_manager import ChannelManager
from hybridlink_core.integrity_verifier import IntegrityVerifier
from hybridlink_core.transfer_controller import TransferController

__all__ = [
    "ChunkInfo",
    "TransferMetadata",
    "ChannelStats",
    "TransferConfig",
    "ChunkManager",
    "ChannelManager",
    "IntegrityVerifier",
    "TransferController",
]
