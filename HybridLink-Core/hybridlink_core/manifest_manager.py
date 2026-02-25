"""
Manifest Manager: Persistent checkpoint and state management for transfers.

Enables:
- Tracking completed chunks
- Resume interrupted transfers
- Cleanup after successful completion
- Atomic writes to prevent corruption
"""

import json
import logging
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class ManifestManager:
    """
    Manages persistent transfer manifests.
    
    Stores:
    - Transfer metadata (file size, chunk count, etc)
    - Completed chunks
    - Channel status
    - Resume state
    """

    # Manifest file name and cleanup patterns
    MANIFEST_FILENAME = "transfer.manifest.json"
    TEMP_SUFFIX = ".hybridlink_tmp"
    BACKUP_SUFFIX = ".backup"

    def __init__(self, transfer_id: str, base_dir: Optional[Path] = None):
        """
        Initialize manifest manager.
        
        Args:
            transfer_id: Unique transfer identifier
            base_dir: Base directory for checkpoints (default: user home)
        """
        self.transfer_id = transfer_id
        self.base_dir = base_dir or Path.home()
        self.manifest_path = self.base_dir / f".hybridlink_{transfer_id}.manifest"
        self.temp_dir = self.base_dir / f".hybridlink_{transfer_id}{self.TEMP_SUFFIX}"
        
        # Ensure temp directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.manifest = self._load_or_create_manifest()

    def _load_or_create_manifest(self) -> Dict:
        """Load existing manifest or create new one."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r") as f:
                    manifest = json.load(f)
                logger.info(f"Loaded existing manifest: {self.manifest_path}")
                return manifest
            except Exception as e:
                logger.warning(f"Failed to load manifest, creating new: {e}")
                self.manifest_path.unlink(missing_ok=True)
        
        return {
            "transfer_id": self.transfer_id,
            "created_at": datetime.utcnow().isoformat(),
            "file_path": None,
            "file_size": None,
            "chunk_size": None,
            "total_chunks": None,
            "completed_chunks": {},  # chunk_id -> {"timestamp": iso, "channel": "usb|wifi"}
            "file_hash": None,
            "verified": False,
            "state": "preparing",  # preparing, transferring, paused, completed, failed
            "error_message": None,
            "usb_enabled": True,
            "wifi_enabled": True,
        }

    def initialize_transfer(
        self,
        file_path: str,
        file_size: int,
        chunk_size: int,
        total_chunks: int,
        usb_enabled: bool = True,
        wifi_enabled: bool = True,
    ) -> None:
        """
        Initialize manifest for a new transfer.
        
        Args:
            file_path: Path to file being transferred
            file_size: Total file size in bytes
            chunk_size: Size of each chunk
            total_chunks: Total number of chunks
            usb_enabled: USB channel enabled
            wifi_enabled: WiFi channel enabled
        """
        self.manifest.update({
            "file_path": str(file_path),
            "file_size": file_size,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "usb_enabled": usb_enabled,
            "wifi_enabled": wifi_enabled,
            "state": "transferring",
        })
        self._save_manifest()
        logger.info(f"Initialized transfer: {file_path} ({file_size} bytes)")

    def record_chunk_completed(
        self,
        chunk_id: int,
        channel: str = "unknown",
    ) -> None:
        """
        Record that a chunk was completed.
        
        Args:
            chunk_id: Chunk ID
            channel: Channel that completed it ("usb" or "wifi")
        """
        self.manifest["completed_chunks"][str(chunk_id)] = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
        }
        self._save_manifest()

    def get_completed_chunks(self) -> Set[int]:
        """Get set of completed chunk IDs."""
        return set(int(cid) for cid in self.manifest.get("completed_chunks", {}))

    def get_pending_chunks(self, total_chunks: int) -> Set[int]:
        """Get set of pending (not yet completed) chunk IDs."""
        completed = self.get_completed_chunks()
        return set(range(total_chunks)) - completed

    def set_transfer_state(self, state: str, error: Optional[str] = None) -> None:
        """
        Update transfer state.
        
        Args:
            state: New state (preparing, transferring, paused, completed, failed)
            error: Optional error message
        """
        self.manifest["state"] = state
        if error:
            self.manifest["error_message"] = error
        self._save_manifest()
        logger.info(f"Transfer state: {state}")

    def record_file_hash(self, file_hash: str, verified: bool = False) -> None:
        """
        Record the file hash and verification status.
        
        Args:
            file_hash: SHA256 hash of file
            verified: Whether hash has been verified
        """
        self.manifest["file_hash"] = file_hash
        self.manifest["verified"] = verified
        self._save_manifest()

    def get_progress(self) -> Dict:
        """
        Get transfer progress summary.
        
        Returns:
            Dict with state, completed_chunks, total_chunks, percentage
        """
        total = self.manifest.get("total_chunks", 0)
        completed = len(self.get_completed_chunks())
        return {
            "state": self.manifest.get("state", "unknown"),
            "completed_chunks": completed,
            "total_chunks": total,
            "percentage": (completed / total * 100) if total > 0 else 0,
            "file_path": self.manifest.get("file_path"),
            "file_size": self.manifest.get("file_size"),
        }

    def can_resume(self) -> bool:
        """
        Check if transfer can be resumed.
        
        Returns:
            True if manifest exists and has pending chunks
        """
        total = self.manifest.get("total_chunks", 0)
        if total == 0:
            return False
        
        completed = len(self.get_completed_chunks())
        return completed < total and completed > 0

    def cleanup(self) -> None:
        """
        Clean up manifest and temporary files after successful transfer.
        
        Removes:
        - Manifest file
        - Temporary chunk directory
        """
        try:
            # Remove manifest
            if self.manifest_path.exists():
                self.manifest_path.unlink()
                logger.info(f"Removed manifest: {self.manifest_path}")
            
            # Remove temp directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup: {e}")

    def _save_manifest(self) -> None:
        """
        Save manifest to file with atomic write.
        
        Uses temporary file + rename to prevent corruption on crash.
        """
        try:
            # Write to temporary file first
            temp_path = self.manifest_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(self.manifest, f, indent=2)
            
            # Atomically rename (Windows API handles this safely)
            temp_path.replace(self.manifest_path)
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
            raise

    def get_temp_chunk_path(self, chunk_id: int) -> Path:
        """
        Get path for temporary chunk file.
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            Path for storing this chunk
        """
        return self.temp_dir / f"chunk_{chunk_id:06d}.tmp"

    def list_temp_chunks(self) -> list:
        """List all temporary chunk files."""
        if not self.temp_dir.exists():
            return []
        return sorted(self.temp_dir.glob("chunk_*.tmp"))


class ReceiveManifestManager:
    """
    Special manifest manager for receive operations.
    
    Tracks:
    - Received chunks in temporary storage
    - Safe merge ordering
    - Resume state
    """

    def __init__(self, transfer_id: str, destination: str):
        """
        Initialize receive manifest.
        
        Args:
            transfer_id: Transfer ID
            destination: Final destination file path
        """
        self.transfer_id = transfer_id
        self.destination = Path(destination)
        self.base_manifest = ManifestManager(transfer_id)
        
    def store_chunk(self, chunk_id: int, data: bytes) -> Path:
        """
        Store received chunk safely.
        
        Args:
            chunk_id: Chunk ID
            data: Chunk data bytes
            
        Returns:
            Path where chunk was stored
        """
        chunk_path = self.base_manifest.get_temp_chunk_path(chunk_id)
        with open(chunk_path, "wb") as f:
            f.write(data)
        self.base_manifest.record_chunk_completed(chunk_id, channel="received")
        return chunk_path

    def merge_chunks(self) -> bool:
        """
        Merge all received chunks into final destination.
        
        Writes chunks in order, avoiding memory buffering.
        
        Returns:
            True if successful
        """
        try:
            chunks = self.base_manifest.get_completed_chunks()
            total_chunks = self.base_manifest.manifest.get("total_chunks", 0)
            
            if len(chunks) != total_chunks:
                logger.error(f"Cannot merge: expected {total_chunks} chunks, got {len(chunks)}")
                return False
            
            # Merge sequentially to avoid memory issues
            with open(self.destination, "wb") as dest_file:
                for chunk_id in range(total_chunks):
                    chunk_path = self.base_manifest.get_temp_chunk_path(chunk_id)
                    if not chunk_path.exists():
                        logger.error(f"Missing chunk: {chunk_id}")
                        return False
                    
                    with open(chunk_path, "rb") as chunk_file:
                        data = chunk_file.read()
                        dest_file.write(data)
            
            logger.info(f"Successfully merged chunks into: {self.destination}")
            return True
        except Exception as e:
            logger.error(f"Failed to merge chunks: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up after successful receive transfer."""
        self.base_manifest.cleanup()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test manifest manager
    manifest = ManifestManager("TEST-001")
    manifest.initialize_transfer(
        file_path="test.bin",
        file_size=104857600,  # 100MB
        chunk_size=4194304,   # 4MB
        total_chunks=25,
    )
    
    # Simulate chunk completion
    for i in range(10):
        manifest.record_chunk_completed(i, channel="usb" if i % 2 else "wifi")
    
    progress = manifest.get_progress()
    print(f"\nProgress: {progress['completed_chunks']}/{progress['total_chunks']} "
          f"({progress['percentage']:.1f}%)")
    print(f"Can resume: {manifest.can_resume()}")
