"""
MultiChannelScheduler: Dynamically assigns chunks to fastest available channels.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import time

from hybridlink_core.chunk_manager import ChunkManager
from hybridlink_core.channel_manager import ChannelManager
from hybridlink_core.models import ChunkRequest, ChunkResponse
from hybridlink_core.config import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


@dataclass
class ScheduledChunk:
    """A chunk scheduled for transfer."""

    chunk_id: int
    channel_type: str
    attempts: int = 0
    scheduled_time: float = 0.0


class MultiChannelScheduler:
    """
    Intelligently schedules chunk transfers across multiple channels.
    
    Responsibilities:
    - Assign chunks to fastest available channels
    - Handle channel disconnection and chunk reallocation
    - Implement retry logic for failed transfers
    - Maintain transfer progress across channels
    - Provide load balancing
    """

    def __init__(
        self,
        chunk_manager: ChunkManager,
        channel_manager: ChannelManager,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialize MultiChannelScheduler.
        
        Args:
            chunk_manager: ChunkManager instance
            channel_manager: ChannelManager instance
            max_retries: Maximum retries per chunk
        """
        self.chunk_manager = chunk_manager
        self.channel_manager = channel_manager
        self.max_retries = max_retries

        self.scheduled_chunks: Dict[int, ScheduledChunk] = {}
        self.failed_chunks: List[int] = []
        self.pending_queue: asyncio.Queue = None

    async def initialize(self) -> None:
        """Initialize scheduler (call after channel setup)."""
        self.pending_queue = asyncio.Queue()

        # Add all pending chunks to queue
        for chunk in self.chunk_manager.get_pending_chunks():
            await self.pending_queue.put(chunk.chunk_id)

        logger.info(
            f"Scheduler initialized with {self.pending_queue.qsize()} pending chunks"
        )

    async def schedule_transfers(
        self, concurrent_transfers: int = 2
    ) -> Dict[str, List[ChunkRequest]]:
        """
        Schedule transfers across available channels.
        
        Assigns chunks to channels based on performance metrics.
        
        Args:
            concurrent_transfers: Max concurrent transfers per channel
            
        Returns:
            Dict mapping channel_type to list of ChunkRequest
        """
        schedule: Dict[str, List[ChunkRequest]] = {}

        available_channels = await self.channel_manager.get_available_channels()
        if not available_channels:
            logger.warning("No available channels for scheduling")
            return schedule

        # Initialize schedule for each channel
        for channel_type in available_channels:
            schedule[channel_type] = []

        # Get pending chunks
        pending_chunks = self.chunk_manager.get_pending_chunks()
        if not pending_chunks:
            logger.info("No pending chunks to schedule")
            return schedule

        # Assign chunks to channels based on speed
        channel_speeds = {}
        for channel_type in available_channels:
            metrics = self.channel_manager.metrics[channel_type]
            channel_speeds[channel_type] = metrics.current_speed_mbps if metrics.speed_history else 0

        chunk_count = 0
        for chunk in pending_chunks:
            if chunk_count >= concurrent_transfers * len(available_channels):
                break  # Respect concurrent transfer limit

            # Select fastest available channel (round-robin if speeds are similar)
            fastest_channel = self._select_best_channel(
                available_channels, channel_speeds
            )

            if fastest_channel:
                chunk_request = ChunkRequest(
                    transfer_id=self.chunk_manager.transfer_id,
                    chunk_id=chunk.chunk_id,
                    offset=chunk.offset,
                    size=chunk.size,
                    channel_type=fastest_channel,
                    timestamp=time.time(),
                )

                schedule[fastest_channel].append(chunk_request)
                self.scheduled_chunks[chunk.chunk_id] = ScheduledChunk(
                    chunk_id=chunk.chunk_id,
                    channel_type=fastest_channel,
                    attempts=0,
                    scheduled_time=time.time(),
                )

                # Update channel speed to distribute load
                channel_speeds[fastest_channel] *= 0.9  # Slight penalty for load balancing

                chunk_count += 1

        logger.debug(
            f"Scheduled {chunk_count} chunks across {len(schedule)} channels"
        )
        return schedule

    def _select_best_channel(
        self, available_channels: List[str], channel_speeds: Dict[str, float]
    ) -> Optional[str]:
        """
        Select the best channel for next chunk.
        
        Considers speed, error rate, and current load.
        
        Args:
            available_channels: List of available channel types
            channel_speeds: Dict of current speeds per channel
            
        Returns:
            Channel type to use, or None if no channels available
        """
        if not available_channels:
            return None

        best_channel = None
        best_score = -1

        for channel_type in available_channels:
            metrics = self.channel_manager.metrics[channel_type]

            # Calculate score: speed - penalty for errors
            speed = channel_speeds.get(channel_type, 0)
            error_penalty = metrics.error_count * 10  # Each error reduces score by 10

            score = speed - error_penalty

            if score > best_score:
                best_score = score
                best_channel = channel_type

        return best_channel

    async def handle_chunk_success(
        self, chunk_id: int, bytes_transferred: int, channel_type: str
    ) -> None:
        """
        Handle successful chunk transfer.
        
        Args:
            chunk_id: ID of transferred chunk
            bytes_transferred: Number of bytes sent
            channel_type: Channel used for transfer
        """
        self.chunk_manager.mark_transferred(chunk_id)
        self.channel_manager.record_transfer(channel_type, bytes_transferred)

        if chunk_id in self.scheduled_chunks:
            scheduled = self.scheduled_chunks[chunk_id]
            logger.debug(
                f"Chunk {chunk_id} transferred on {channel_type} "
                f"(attempt {scheduled.attempts + 1})"
            )

    async def handle_chunk_failure(
        self, chunk_id: int, channel_type: str, error: str = ""
    ) -> bool:
        """
        Handle failed chunk transfer and reschedule if possible.
        
        Args:
            chunk_id: ID of failed chunk
            channel_type: Channel that failed
            error: Error message
            
        Returns:
            True if chunk will be retried, False if max retries exceeded
        """
        self.channel_manager.record_transfer(channel_type, 0, error=error)

        if chunk_id not in self.scheduled_chunks:
            scheduled = ScheduledChunk(
                chunk_id=chunk_id, channel_type=channel_type, attempts=1
            )
            self.scheduled_chunks[chunk_id] = scheduled
        else:
            self.scheduled_chunks[chunk_id].attempts += 1

        attempts = self.scheduled_chunks[chunk_id].attempts

        if attempts >= self.max_retries:
            logger.error(
                f"Chunk {chunk_id} failed on {channel_type} "
                f"(attempt {attempts}/{self.max_retries})"
            )
            self.failed_chunks.append(chunk_id)
            return False

        logger.warning(
            f"Chunk {chunk_id} failed on {channel_type}, "
            f"retrying (attempt {attempts}/{self.max_retries})..."
        )

        # Reset chunk for retry
        self.chunk_manager.reset_chunk(chunk_id)

        # Re-queue for scheduling
        await asyncio.sleep(RETRY_DELAY)
        await self.pending_queue.put(chunk_id)

        return True

    async def check_channel_health(self) -> None:
        """
        Periodically check channel health and redistribute failed chunks.
        """
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                # Reallocate chunks from failed channels
                for chunk_id, scheduled in list(self.scheduled_chunks.items()):
                    channel_type = scheduled.channel_type

                    # If channel went down, reschedule chunk
                    if not await self.channel_manager.is_channel_available(channel_type):
                        logger.warning(
                            f"Channel {channel_type} is down, "
                            f"rescheduling chunk {chunk_id}"
                        )

                        chunk_info = self.chunk_manager.get_chunk_info(chunk_id)
                        if chunk_info and not chunk_info.transferred:
                            self.chunk_manager.reset_chunk(chunk_id)
                            await self.pending_queue.put(chunk_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in channel health check: {e}")

    def get_statistics(self) -> dict:
        """Get scheduler statistics."""
        transferred, total = self.chunk_manager.get_transfer_progress()

        return {
            "total_chunks": total,
            "chunks_transferred": transferred,
            "chunks_pending": self.pending_queue.qsize() if self.pending_queue else 0,
            "chunks_failed": len(self.failed_chunks),
            "scheduled_chunks": len(self.scheduled_chunks),
            "transfer_percent": (transferred / total * 100) if total > 0 else 0,
        }

    def get_failed_chunks(self) -> List[int]:
        """Get list of chunks that failed all retries."""
        return self.failed_chunks.copy()
