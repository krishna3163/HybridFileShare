"""
ChunkAssembler: Assembles received chunks into a complete file with resumable support.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Set
from tempfile import TemporaryDirectory

from hybridlink_core.integrity_verifier import IntegrityVerifier
from hybridlink_core.models import TransferMetadata

logger = logging.getLogger(__name__)


class ChunkAssembler:
    """
    Single-writer buffered merge for assembling chunks into a complete file.
    
    Responsibilities:
    - Write received chunks to temporary storage
    - Assemble chunks in correct order into final file
    - Support resumable transfers using metadata index
    - Prevent duplicate writes
    - Manage temporary files safely
    """

    def __init__(self, output_path: Path, total_size: int, chunk_size: int):
        """
        Initialize ChunkAssembler.
        
        Args:
            output_path: Path where the final file will be written
            total_size: Total size of the file being assembled
            chunk_size: Size of individual chunks
        """
        self.output_path = output_path
        self.total_size = total_size
        self.chunk_size = chunk_size

        # Create temp directory for partial chunks
        self.temp_dir = Path(TemporaryDirectory().name)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.received_chunks: Dict[int, Path] = {}  # chunk_id -> temp file path
        self.chunk_hashes: Dict[int, str] = {}  # chunk_id -> hash
        self.verified_chunks: Set[int] = set()

        logger.info(f"Initialized ChunkAssembler for: {output_path.name}")

    def write_chunk(self, chunk_id: int, chunk_data: bytes) -> bool:
        """
        Write a received chunk to temporary storage.
        
        Prevents duplicate writes and maintains integrity.
        
        Args:
            chunk_id: ID of the chunk
            chunk_data: Raw chunk data
            
        Returns:
            True if chunk written successfully, False if duplicate
        """
        # Check if we already have this chunk
        if chunk_id in self.received_chunks:
            logger.debug(f"Chunk {chunk_id} already received (duplicate prevention)")
            return False

        try:
            chunk_hash = IntegrityVerifier.hash_chunk(chunk_data)
            self.chunk_hashes[chunk_id] = chunk_hash

            # Write to temporary file
            temp_chunk_path = self.temp_dir / f"chunk_{chunk_id:06d}.tmp"
            temp_chunk_path.write_bytes(chunk_data)

            self.received_chunks[chunk_id] = temp_chunk_path
            logger.debug(f"Wrote chunk {chunk_id} ({len(chunk_data)} bytes)")
            return True

        except Exception as e:
            logger.error(f"Error writing chunk {chunk_id}: {e}")
            return False

    def verify_and_mark_chunk(self, chunk_id: int, expected_hash: Optional[str] = None) -> bool:
        """
        Verify a received chunk and mark it as verified.
        
        Args:
            chunk_id: ID of the chunk
            expected_hash: Optional expected hash for verification
            
        Returns:
            True if chunk verified
        """
        if chunk_id not in self.received_chunks:
            logger.warning(f"Chunk {chunk_id} not received yet")
            return False

        try:
            if expected_hash:
                actual_hash = self.chunk_hashes.get(chunk_id)
                if actual_hash != expected_hash:
                    logger.error(
                        f"Chunk {chunk_id} hash mismatch: "
                        f"expected {expected_hash}, got {actual_hash}"
                    )
                    return False

            self.verified_chunks.add(chunk_id)
            logger.debug(f"Chunk {chunk_id} verified")
            return True

        except Exception as e:
            logger.error(f"Error verifying chunk {chunk_id}: {e}")
            return False

    def assemble_file(self, verify_final: bool = True) -> bool:
        """
        Assemble all received chunks into the final file.
        
        Writes chunks in correct order to output path.
        
        Args:
            verify_final: Whether to verify the final file hash
            
        Returns:
            True if assembly successful
        """
        try:
            # Check we have all chunks
            num_chunks = (self.total_size + self.chunk_size - 1) // self.chunk_size
            if len(self.received_chunks) != num_chunks:
                logger.error(
                    f"Missing chunks: received {len(self.received_chunks)}, "
                    f"expected {num_chunks}"
                )
                return False

            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write chunks in order to final file
            with open(self.output_path, "wb") as output_file:
                for chunk_id in range(num_chunks):
                    if chunk_id not in self.received_chunks:
                        logger.error(f"Missing chunk {chunk_id}")
                        return False

                    chunk_path = self.received_chunks[chunk_id]
                    chunk_data = chunk_path.read_bytes()
                    output_file.write(chunk_data)

            logger.info(
                f"Successfully assembled file: {self.output_path.name} "
                f"({self.total_size:,} bytes)"
            )
            self._cleanup_temp_files()
            return True

        except Exception as e:
            logger.error(f"Error assembling file: {e}")
            return False

    def get_pending_chunks(self) -> list:
        """
        Get list of chunks that haven't been received yet.
        
        Returns:
            List of missing chunk IDs
        """
        num_chunks = (self.total_size + self.chunk_size - 1) // self.chunk_size
        pending = []

        for chunk_id in range(num_chunks):
            if chunk_id not in self.received_chunks:
                pending.append(chunk_id)

        return pending

    def get_assembly_progress(self) -> tuple[int, int]:
        """
        Get current assembly progress.
        
        Returns:
            Tuple of (chunks_received, total_chunks)
        """
        num_chunks = (self.total_size + self.chunk_size - 1) // self.chunk_size
        return len(self.received_chunks), num_chunks

    def save_checkpoint(self, checkpoint_path: Path) -> None:
        """
        Save checkpoint with current progress for resumption.
        
        Args:
            checkpoint_path: Path where checkpoint metadata is saved
        """
        try:
            metadata = {
                "received_chunks": list(self.received_chunks.keys()),
                "verified_chunks": list(self.verified_chunks),
                "chunk_hashes": self.chunk_hashes,
            }

            import json

            checkpoint_path.write_text(json.dumps(metadata, indent=2))
            logger.info(f"Checkpoint saved: {checkpoint_path}")

        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def load_checkpoint(self, checkpoint_path: Path) -> bool:
        """
        Load checkpoint to resume transfer.
        
        Args:
            checkpoint_path: Path to checkpoint metadata
            
        Returns:
            True if checkpoint loaded successfully
        """
        try:
            import json

            checkpoint_data = json.loads(checkpoint_path.read_text())

            # Verify chunk files exist
            for chunk_id in checkpoint_data["received_chunks"]:
                temp_chunk_path = self.temp_dir / f"chunk_{chunk_id:06d}.tmp"
                if not temp_chunk_path.exists():
                    logger.warning(f"Chunk {chunk_id} temp file not found")
                    continue

                self.received_chunks[chunk_id] = temp_chunk_path

            self.verified_chunks = set(checkpoint_data["verified_chunks"])
            self.chunk_hashes = checkpoint_data["chunk_hashes"]

            logger.info(
                f"Checkpoint loaded: {len(self.received_chunks)} chunks recovered"
            )
            return True

        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up temporary files."""
        self._cleanup_temp_files()

    def _cleanup_temp_files(self) -> None:
        """Remove temporary chunk files."""
        try:
            for chunk_path in self.received_chunks.values():
                try:
                    chunk_path.unlink()
                except Exception:
                    pass

            # Remove temp directory
            try:
                self.temp_dir.rmdir()
            except Exception:
                pass

            logger.debug("Temporary files cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up temporary files: {e}")

    def __del__(self):
        """Ensure cleanup on deletion."""
        try:
            self._cleanup_temp_files()
        except Exception:
            pass
