"""
ProgressReporter: Tracks and reports transfer progress with speed and ETA calculations.
"""

import logging
import time
from typing import Callable, Optional
from dataclasses import dataclass, field

from hybridlink_core.models import ProgressUpdate, ChannelStats
from hybridlink_core.channel_manager import ChannelManager
from hybridlink_core.chunk_manager import ChunkManager

logger = logging.getLogger(__name__)


@dataclass
class TransferMetrics:
    """Metrics tracked during transfer."""

    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    bytes_transferred: int = 0
    previous_bytes: int = 0
    chunk_speed_samples: list = field(default_factory=list)

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time since start."""
        return time.time() - self.start_time

    @property
    def current_speed_mbps(self) -> float:
        """Calculate current speed in Mbps."""
        if self.elapsed_seconds == 0:
            return 0.0

        bytes_transferred = self.bytes_transferred
        elapsed = self.elapsed_seconds

        if elapsed < 1.0:
            return 0.0  # Not enough time for measurement

        speed_bps = bytes_transferred / elapsed
        return (speed_bps * 8) / 1_000_000  # Convert to Mbps

    @property
    def average_speed_mbps(self) -> float:
        """Get average speed in Mbps."""
        return self.current_speed_mbps

    def calculate_eta(self, total_bytes: int) -> Optional[int]:
        """
        Calculate estimated time to completion in seconds.
        
        Args:
            total_bytes: Total bytes to transfer
            
        Returns:
            ETA in seconds, or None if cannot calculate
        """
        speed_mbps = self.current_speed_mbps
        if speed_mbps == 0:
            return None

        bytes_remaining = total_bytes - self.bytes_transferred
        if bytes_remaining <= 0:
            return 0

        # Convert speed to bytes per second
        speed_bps = (speed_mbps * 1_000_000) / 8
        eta_seconds = bytes_remaining / speed_bps

        return int(eta_seconds)


class ProgressReporter:
    """
    Tracks and reports transfer progress.
    
    Responsibilities:
    - Calculate transfer speed
    - Estimate time to completion
    - Track per-channel progress
    - Provide progress callbacks
    """

    def __init__(
        self,
        transfer_id: str,
        total_bytes: int,
        chunk_manager: ChunkManager,
        channel_manager: ChannelManager,
    ):
        """
        Initialize ProgressReporter.
        
        Args:
            transfer_id: ID of the transfer
            total_bytes: Total bytes to transfer
            chunk_manager: ChunkManager instance
            channel_manager: ChannelManager instance
        """
        self.transfer_id = transfer_id
        self.total_bytes = total_bytes
        self.chunk_manager = chunk_manager
        self.channel_manager = channel_manager
        self.metrics = TransferMetrics()

        self.progress_callbacks: list[Callable[[ProgressUpdate], None]] = []

        logger.info(f"Initialized ProgressReporter for {transfer_id}")

    def add_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """
        Add a callback to be called on progress updates.
        
        Args:
            callback: Callable that accepts ProgressUpdate
        """
        self.progress_callbacks.append(callback)

    def update_progress(self, bytes_transferred: int, state: str = "transferring") -> ProgressUpdate:
        """
        Update progress and trigger callbacks.
        
        Args:
            bytes_transferred: Total bytes transferred so far
            state: Current transfer state
            
        Returns:
            ProgressUpdate with current metrics
        """
        self.metrics.bytes_transferred = bytes_transferred
        self.metrics.last_update = time.time()

        # Get chunk progress
        chunks_completed, total_chunks = self.chunk_manager.get_transfer_progress()

        # Calculate ETA
        eta = self.metrics.calculate_eta(self.total_bytes)

        # Build channel stats
        channel_stats = {}
        for channel_type, stats in self.channel_manager.get_all_stats().items():
            if stats:
                channel_stats[channel_type] = stats

        # Create progress update
        progress = ProgressUpdate(
            transfer_id=self.transfer_id,
            bytes_transferred=bytes_transferred,
            total_bytes=self.total_bytes,
            elapsed_seconds=self.metrics.elapsed_seconds,
            chunks_completed=chunks_completed,
            total_chunks=total_chunks,
            current_speed_mbps=self.metrics.current_speed_mbps,
            eta_seconds=eta,
            channels=channel_stats,
            state=state,
        )

        # Trigger callbacks
        for callback in self.progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

        return progress

    def get_status(self) -> dict:
        """Get detailed status information."""
        chunks_completed, total_chunks = self.chunk_manager.get_transfer_progress()
        progress_percent = (chunks_completed / total_chunks * 100) if total_chunks > 0 else 0

        return {
            "transfer_id": self.transfer_id,
            "bytes_transferred": self.metrics.bytes_transferred,
            "total_bytes": self.total_bytes,
            "bytes_remaining": self.total_bytes - self.metrics.bytes_transferred,
            "transfer_percent": (
                self.metrics.bytes_transferred / self.total_bytes * 100
                if self.total_bytes > 0
                else 0
            ),
            "chunks_completed": chunks_completed,
            "total_chunks": total_chunks,
            "chunks_percent": progress_percent,
            "elapsed_seconds": self.metrics.elapsed_seconds,
            "speed_mbps": self.metrics.current_speed_mbps,
            "eta_seconds": self.metrics.calculate_eta(self.total_bytes),
            "channel_summary": self.channel_manager.get_summary(),
        }

    def format_progress_bar(
        self, width: int = 40, show_percent: bool = True
    ) -> str:
        """
        Format a text-based progress bar.
        
        Args:
            width: Width of progress bar in characters
            show_percent: Whether to show percentage
            
        Returns:
            Formatted progress bar string
        """
        if self.total_bytes == 0:
            filled = 0
        else:
            filled = int(
                (self.metrics.bytes_transferred / self.total_bytes) * width
            )

        bar = "█" * filled + "░" * (width - filled)
        percent = (
            (self.metrics.bytes_transferred / self.total_bytes * 100)
            if self.total_bytes > 0
            else 0
        )

        if show_percent:
            return f"[{bar}] {percent:.1f}%"
        else:
            return f"[{bar}]"

    def format_speed(self) -> str:
        """Format current speed as human-readable string."""
        speed = self.metrics.current_speed_mbps
        if speed >= 1000:
            return f"{speed / 1000:.2f} Gbps"
        else:
            return f"{speed:.2f} Mbps"

    def format_eta(self) -> str:
        """Format ETA as human-readable string."""
        eta = self.metrics.calculate_eta(self.total_bytes)
        if eta is None:
            return "calculating..."

        if eta < 60:
            return f"{eta}s"
        elif eta < 3600:
            return f"{eta // 60}m {eta % 60}s"
        else:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            return f"{hours}h {minutes}m"

    def format_size(self, size: int) -> str:
        """Format size as human-readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def print_summary(self) -> None:
        """Print a summary of transfer progress."""
        status = self.get_status()

        logger.info("=" * 60)
        logger.info(f"Transfer: {self.transfer_id}")
        logger.info(f"Progress: {status['transfer_percent']:.1f}%")
        logger.info(
            f"  {self.format_size(status['bytes_transferred'])} / "
            f"{self.format_size(status['total_bytes'])}"
        )
        logger.info(f"Speed: {self.format_speed()}")
        logger.info(f"ETA: {self.format_eta()}")
        logger.info(f"Chunks: {status['chunks_completed']} / {status['total_chunks']}")
        logger.info(
            f"Elapsed: {int(status['elapsed_seconds'])}s "
            f"({status['elapsed_seconds'] / 60:.1f}m)"
        )

        # Channel info
        channel_summary = status["channel_summary"]
        if channel_summary["channels"]:
            logger.info("Channels:")
            for channel_type, stats in channel_summary["channels"].items():
                logger.info(
                    f"  {channel_type}: {stats['transfer_speed_mbps']:.2f} Mbps "
                    f"({self.format_size(stats['bytes_transferred'])})"
                )

        logger.info("=" * 60)
