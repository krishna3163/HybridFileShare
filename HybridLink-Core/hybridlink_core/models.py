"""
Data models for HybridLink-Core using Pydantic.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from pydantic import BaseModel, Field


class ChunkInfo(BaseModel):
    """Information about a single chunk."""

    chunk_id: int
    offset: int
    size: int
    hash: Optional[str] = None
    transferred: bool = False
    attempts: int = 0


class ChannelStats(BaseModel):
    """Statistics for a single channel."""

    channel_type: str
    available: bool = False
    bytes_transferred: int = 0
    transfer_speed_mbps: float = 0.0
    last_activity: Optional[str] = None
    error_count: int = 0


class TransferMetadata(BaseModel):
    """Metadata for a transfer session, used for resumption."""

    transfer_id: str
    file_path: str
    file_size: int
    total_chunks: int
    chunk_size: int
    chunks_transferred: Dict[int, bool] = Field(default_factory=dict)
    start_time: str
    last_updated: str
    mode: str  # "send" or "receive"
    destination_path: Optional[str] = None
    file_hash: Optional[str] = None
    verified_chunks: List[int] = Field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "TransferMetadata":
        """Deserialize from JSON."""
        return cls.model_validate_json(json_str)

    def save_to_file(self, path: Path) -> None:
        """Save metadata checkpoint to file."""
        path.write_text(self.to_json())

    @classmethod
    def load_from_file(cls, path: Path) -> "TransferMetadata":
        """Load metadata checkpoint from file."""
        return cls.from_json(path.read_text())


class TransferConfig(BaseModel):
    """Configuration for a transfer session."""

    chunk_size: int = 4 * 1024 * 1024  # 4MB default
    max_retries: int = 3
    usb_enabled: bool = True
    wifi_enabled: bool = True
    usb_host: str = "localhost"
    usb_port: int = 9000
    wifi_port: int = 9001
    wifi_timeout: float = 30.0
    channel_timeout: float = 60.0
    verify_integrity: bool = True


class ProgressUpdate(BaseModel):
    """Progress update message."""

    transfer_id: str
    bytes_transferred: int
    total_bytes: int
    elapsed_seconds: float
    chunks_completed: int
    total_chunks: int
    current_speed_mbps: float
    eta_seconds: Optional[int] = None
    channels: Dict[str, ChannelStats] = Field(default_factory=dict)
    state: str = "transferring"

    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_transferred / self.total_bytes) * 100


@dataclass
class ChunkRequest:
    """Request to transfer a specific chunk."""

    transfer_id: str
    chunk_id: int
    offset: int
    size: int
    channel_type: str
    timestamp: float = field(default_factory=__import__("time").time)


@dataclass
class ChunkResponse:
    """Response after chunk transfer."""

    transfer_id: str
    chunk_id: int
    success: bool
    bytes_transferred: int
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=__import__("time").time)
