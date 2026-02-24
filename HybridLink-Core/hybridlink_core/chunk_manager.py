"""
ChunkManager: Splits files into indexed chunks and tracks their state.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
import uuid

from hybridlink_core.models import ChunkInfo
from hybridlink_core.config import DEFAULT_CHUNK_SIZE

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for chunk file operations."""

    file_path: Path
    file_size: int
    chunk_size: int
    total_chunks: int


class ChunkManager:
    """
    Manages file chunking and state tracking.
    
    Splits large files into fixed-size chunks (default 4MB) and maintains
    a state map of which chunks have been transferred.
    """

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Initialize ChunkManager.
        
        Args:
            chunk_size: Size of each chunk in bytes (default 4MB)
        """
        self.chunk_size = chunk_size
        self.chunks: Dict[int, ChunkInfo] = {}
        self.file_path: Optional[Path] = None
        self.file_size: int = 0
        self.transfer_id: str = ""

    def initialize_file(self, file_path: Path, transfer_id: str = "") -> None:
        """
        Initialize chunking for a file.
        
        Args:
            file_path: Path to the file to chunk
            transfer_id: Optional transfer identifier
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.file_path = file_path
        self.file_size = file_path.stat().st_size
        self.transfer_id = transfer_id or str(uuid.uuid4())[:8]

        self._create_chunks()
        logger.info(
            f"Initialized {len(self.chunks)} chunks for file: {file_path.name} "
            f"(size: {self.file_size:,} bytes)"
        )

    def _create_chunks(self) -> None:
        """Create chunk information based on file size and chunk size."""
        self.chunks = {}
        num_chunks = (self.file_size + self.chunk_size - 1) // self.chunk_size

        for i in range(num_chunks):
            offset = i * self.chunk_size
            size = min(self.chunk_size, self.file_size - offset)
            self.chunks[i] = ChunkInfo(
                chunk_id=i, offset=offset, size=size, transferred=False, attempts=0
            )

    def get_chunk_data(self, chunk_id: int) -> bytes:
        """
        Read chunk data from file.
        
        Args:
            chunk_id: ID of the chunk to read
            
        Returns:
            Raw chunk data
            
        Raises:
            ValueError: If chunk_id is invalid
            FileNotFoundError: If file no longer exists
        """
        if chunk_id not in self.chunks:
            raise ValueError(f"Invalid chunk_id: {chunk_id}")

        if not self.file_path or not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        chunk_info = self.chunks[chunk_id]

        with open(self.file_path, "rb") as f:
            f.seek(chunk_info.offset)
            return f.read(chunk_info.size)

    def mark_transferred(self, chunk_id: int, hash_value: Optional[str] = None) -> None:
        """
        Mark a chunk as successfully transferred.
        
        Args:
            chunk_id: ID of the chunk
            hash_value: Optional hash of the chunk for verification
        """
        if chunk_id in self.chunks:
            self.chunks[chunk_id].transferred = True
            if hash_value:
                self.chunks[chunk_id].hash = hash_value
            logger.debug(f"Chunk {chunk_id} marked as transferred")

    def mark_failed(self, chunk_id: int) -> None:
        """
        Mark a chunk transfer attempt as failed (increments attempts counter).
        
        Args:
            chunk_id: ID of the chunk
        """
        if chunk_id in self.chunks:
            self.chunks[chunk_id].attempts += 1
            logger.debug(
                f"Chunk {chunk_id} failed (attempt #{self.chunks[chunk_id].attempts})"
            )

    def get_pending_chunks(self) -> List[ChunkInfo]:
        """
        Get list of chunks that haven't been transferred yet.
        
        Returns:
            List of pending ChunkInfo objects
        """
        return [c for c in self.chunks.values() if not c.transferred]

    def get_chunk_info(self, chunk_id: int) -> Optional[ChunkInfo]:
        """Get information about a specific chunk."""
        return self.chunks.get(chunk_id)

    def get_all_chunks(self) -> List[ChunkInfo]:
        """Get information about all chunks."""
        return list(self.chunks.values())

    def get_transfer_progress(self) -> tuple[int, int]:
        """
        Get transfer progress.
        
        Returns:
            Tuple of (chunks_transferred, total_chunks)
        """
        transferred = sum(1 for c in self.chunks.values() if c.transferred)
        return transferred, len(self.chunks)

    def get_bytes_transferred(self) -> int:
        """Get total bytes transferred."""
        return sum(c.size for c in self.chunks.values() if c.transferred)

    def reset_chunk(self, chunk_id: int) -> None:
        """
        Reset a chunk's transfer state for retry.
        
        Args:
            chunk_id: ID of the chunk to reset
        """
        if chunk_id in self.chunks:
            self.chunks[chunk_id].transferred = False
            logger.debug(f"Chunk {chunk_id} reset for retry")

    def reset_all(self) -> None:
        """Reset all chunks to untransferred state."""
        for chunk in self.chunks.values():
            chunk.transferred = False
        logger.info("All chunks reset")

    def get_statistics(self) -> dict:
        """Get detailed statistics about chunks."""
        transferred, total = self.get_transfer_progress()
        bytes_transferred = self.get_bytes_transferred()

        return {
            "transfer_id": self.transfer_id,
            "file_path": str(self.file_path) if self.file_path else None,
            "file_size": self.file_size,
            "chunk_size": self.chunk_size,
            "total_chunks": total,
            "chunks_transferred": transferred,
            "bytes_transferred": bytes_transferred,
            "bytes_remaining": self.file_size - bytes_transferred,
            "completion_percent": (transferred / total * 100) if total > 0 else 0,
        }
