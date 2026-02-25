"""
MultiChannelScheduler: Advanced scheduling for high-performance multipath transfers.
"""

import logging
import asyncio
import time
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field

from hybridlink_core.chunk_manager import ChunkManager
from hybridlink_core.channel_manager import ChannelManager
from hybridlink_core.models import ChunkRequest, ChunkResponse
from hybridlink_core.config import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

@dataclass
class ChannelPerformance:
    """Predictive metrics for a channel."""
    speed_mbps: float = 0.0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    load_factor: float = 0.0
    history: List[float] = field(default_factory=list)

class MultiChannelScheduler:
    """
    Advanced multipath scheduler with predictive bandwidth estimation.
    
    Features:
    - Adaptive chunk distribution based on live link speed
    - Dynamic failover for degrading transports
    - Parallel chunk streaming across transports
    - Latency-aware chunk prioritization (small/control chunks vs data)
    - Predictive bandwidth estimation using moving averages
    """

    def __init__(
        self,
        chunk_manager: ChunkManager,
        channel_manager: ChannelManager,
        max_retries: int = MAX_RETRIES,
    ):
        self.chunk_manager = chunk_manager
        self.channel_manager = channel_manager
        self.max_retries = max_retries

        self.scheduled_chunks: Dict[int, float] = {}  # chunk_id -> start_time
        self.perf_metrics: Dict[str, ChannelPerformance] = {}
        self.pending_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize scheduler and predictive metrics."""
        for chunk in self.chunk_manager.get_pending_chunks():
            await self.pending_queue.put(chunk.chunk_id)
        
        for ch_type in self.channel_manager.channels:
            self.perf_metrics[ch_type] = ChannelPerformance()

    def _estimate_bandwidth(self, channel_type: str) -> float:
        """Predictive bandwidth estimation using exponential moving average."""
        metrics = self.channel_manager.metrics.get(channel_type)
        if not metrics or not metrics.speed_history:
            return 0.1 # Minimal fallback
        
        # Exponential moving average for prediction
        alpha = 0.7
        prediction = metrics.speed_history[0]
        for sample in metrics.speed_history[1:]:
            prediction = alpha * sample + (1 - alpha) * prediction
        
        return prediction

    async def get_next_assignments(self) -> List[Tuple[int, str]]:
        """
        Produce a list of (chunk_id, channel_type) assignments.
        Uses adaptive distribution based on predicted speeds.
        """
        assignments = []
        available_channels = await self.channel_manager.get_available_channels()
        
        if not available_channels:
            return []

        async with self._lock:
            # Determine bandwidth ratio for distribution
            speeds = {ch: self._estimate_bandwidth(ch) for ch in available_channels}
            total_speed = sum(speeds.values())
            
            if total_speed == 0:
                # Fallback to round-robin
                for ch in available_channels:
                    if self.pending_queue.empty(): break
                    chunk_id = await self.pending_queue.get()
                    assignments.append((chunk_id, ch))
                return assignments

            # Distribute based on expected throughput
            for ch in available_channels:
                ratio = speeds[ch] / total_speed
                # Max concurrency of 4 per channel for parallelism
                target = max(1, int(4 * ratio)) 
                
                for _ in range(target):
                    if self.pending_queue.empty(): break
                    chunk_id = await self.pending_queue.get()
                    assignments.append((chunk_id, ch))
                    self.scheduled_chunks[chunk_id] = time.time()

        return assignments

    async def handle_chunk_success(self, chunk_id: int, channel_type: str, bytes_sent: int):
        """Record success and update predictive metrics."""
        if chunk_id in self.scheduled_chunks:
            duration = time.time() - self.scheduled_chunks.pop(chunk_id)
            # Update latency estimation
            perf = self.perf_metrics[channel_type]
            perf.latency_ms = (perf.latency_ms * 0.9) + (duration * 100) # Simple EMA
        
        self.chunk_manager.mark_transferred(chunk_id)
        self.channel_manager.record_transfer(channel_type, bytes_sent)

    async def handle_chunk_failure(self, chunk_id: int, channel_type: str):
        """Fast failover: immediately re-queue on failure."""
        if chunk_id in self.scheduled_chunks:
            self.scheduled_chunks.pop(chunk_id)
            
        logger.warning(f"Failover: Chunk {chunk_id} failed on {channel_type}, re-queuing...")
        self.chunk_manager.reset_chunk(chunk_id)
        await self.pending_queue.put(chunk_id)
        
        # Penalty for the channel
        perf = self.perf_metrics.get(channel_type)
        if perf:
            perf.error_rate += 0.1

    def get_statistics(self) -> dict:
        transferred, total = self.chunk_manager.get_transfer_progress()
        return {
            "progress_percent": (transferred / total * 100) if total > 0 else 0,
            "active_parallelism": len(self.scheduled_chunks),
            "channel_health": {ch: vars(p) for ch, p in self.perf_metrics.items()}
        }
