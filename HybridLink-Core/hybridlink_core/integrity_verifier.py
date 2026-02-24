"""
IntegrityVerifier: SHA-256 based integrity verification for chunks and files.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class IntegrityVerifier:
    """
    Verifies integrity of chunks and complete files using SHA-256.
    
    Capabilities:
    - Calculate SHA-256 hash for chunks
    - Calculate SHA-256 hash for complete files
    - Verify individual chunk integrity
    - Verify complete file after assembly
    """

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """
        Calculate SHA-256 hash of bytes.
        
        Args:
            data: Raw bytes to hash
            
        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_chunk(chunk_data: bytes) -> str:
        """
        Hash a single chunk.
        
        Args:
            chunk_data: Raw chunk data
            
        Returns:
            Hex-encoded SHA-256 hash
        """
        return IntegrityVerifier.hash_bytes(chunk_data)

    @staticmethod
    def hash_file(file_path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
        """
        Calculate SHA-256 hash of an entire file.
        
        For large files, read in chunks to minimize memory usage.
        
        Args:
            file_path: Path to file to hash
            chunk_size: Size of chunks to read (default 4MB)
            
        Returns:
            Hex-encoded SHA-256 hash
            
        Raises:
            FileNotFoundError: If file does not exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        hasher = hashlib.sha256()

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)

        return hasher.hexdigest()

    @staticmethod
    def verify_chunk(chunk_data: bytes, expected_hash: str) -> bool:
        """
        Verify a chunk against its expected hash.
        
        Args:
            chunk_data: Raw chunk data
            expected_hash: Expected SHA-256 hash (hex-encoded)
            
        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = IntegrityVerifier.hash_chunk(chunk_data)
        matches = actual_hash == expected_hash
        
        if not matches:
            logger.warning(
                f"Chunk verification failed: expected {expected_hash}, "
                f"got {actual_hash}"
            )
        
        return matches

    @staticmethod
    def verify_file(file_path: Path, expected_hash: str) -> bool:
        """
        Verify a complete file against its expected hash.
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA-256 hash (hex-encoded)
            
        Returns:
            True if hash matches, False otherwise
        """
        try:
            actual_hash = IntegrityVerifier.hash_file(file_path)
            matches = actual_hash == expected_hash

            if matches:
                logger.info(f"File verification successful: {file_path.name}")
            else:
                logger.error(
                    f"File verification failed: expected {expected_hash}, "
                    f"got {actual_hash}"
                )

            return matches

        except Exception as e:
            logger.error(f"Error verifying file {file_path}: {e}")
            return False

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """
        Calculate and return the hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex-encoded SHA-256 hash
        """
        return IntegrityVerifier.hash_file(file_path)


class ChunkVerifier:
    """Helper class to track and verify multiple chunks."""

    def __init__(self):
        """Initialize ChunkVerifier."""
        self.chunk_hashes: Dict[int, str] = {}
        self.verified_chunks: set = set()

    def add_chunk_hash(self, chunk_id: int, hash_value: str) -> None:
        """
        Register a chunk hash for later verification.
        
        Args:
            chunk_id: ID of the chunk
            hash_value: SHA-256 hash (hex-encoded)
        """
        self.chunk_hashes[chunk_id] = hash_value

    def verify_chunk(self, chunk_id: int, chunk_data: bytes) -> bool:
        """
        Verify a chunk against its registered hash.
        
        Args:
            chunk_id: ID of the chunk
            chunk_data: Raw chunk data
            
        Returns:
            True if hash matches
        """
        if chunk_id not in self.chunk_hashes:
            logger.warning(f"No hash registered for chunk {chunk_id}")
            return False

        expected_hash = self.chunk_hashes[chunk_id]
        actual_hash = IntegrityVerifier.hash_chunk(chunk_data)

        if actual_hash == expected_hash:
            self.verified_chunks.add(chunk_id)
            return True
        else:
            logger.error(
                f"Chunk {chunk_id} verification failed: expected {expected_hash}, "
                f"got {actual_hash}"
            )
            return False

    def get_verified_count(self) -> int:
        """Get number of verified chunks."""
        return len(self.verified_chunks)

    def get_verification_status(self) -> Dict[int, bool]:
        """
        Get verification status for all chunks.
        
        Returns:
            Dict mapping chunk_id to verification status
        """
        status = {}
        for chunk_id in self.chunk_hashes:
            status[chunk_id] = chunk_id in self.verified_chunks
        return status

    def reset(self) -> None:
        """Reset verification state."""
        self.chunk_hashes.clear()
        self.verified_chunks.clear()
