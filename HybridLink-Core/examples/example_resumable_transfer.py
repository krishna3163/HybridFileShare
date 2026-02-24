"""
Example: Resumable Transfer with Checkpoint Support.

This demonstrates how to save and resume interrupted transfers.
"""

import asyncio
import logging
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from hybridlink_core.transfer_controller import TransferController
from hybridlink_core.models import TransferConfig
from hybridlink_core.chunk_assembler import ChunkAssembler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def example_resumable_transfer():
    """Example: Send a file with checkpoint support for resumption."""
    
    # Create a test file (100 MB)
    logger.info("Creating test file (100 MB)...")
    with NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        test_file = Path(tmp.name)
        chunk_size = 1024 * 1024  # 1 MB
        for i in range(100):
            tmp.write(b"X" * chunk_size)
    
    try:
        destination_host = "192.168.1.100"
        
        config = TransferConfig(
            chunk_size=4 * 1024 * 1024,  # 4 MB chunks
            usb_enabled=True,
            wifi_enabled=True,
            verify_integrity=True,
        )
        
        # Create controller
        controller = TransferController(config)
        transfer_id = "resumable_example"
        
        # Initialize sender
        logger.info(f"Initializing sender: {test_file.name}")
        success = await controller.initialize_sender(
            file_path=test_file,
            destination_host=destination_host,
            transfer_id=transfer_id,
        )
        
        if not success:
            logger.error("Failed to initialize sender")
            return False
        
        # Connect channels
        logger.info("Connecting channels...")
        success = await controller.connect_channels()
        
        if not success:
            logger.error("Failed to connect channels")
            return False
        
        # Setup progress tracking
        checkpoint_file = Path(f".{transfer_id}.checkpoint")
        last_checkpoint_bytes = 0
        
        def on_progress(update):
            nonlocal last_checkpoint_bytes
            
            progress_pct = (update.bytes_transferred / update.total_bytes) * 100
            
            logger.info(
                f"Progress: {progress_pct:.1f}% "
                f"({update.bytes_transferred} / {update.total_bytes} bytes) "
                f"Speed: {update.current_speed_mbps:.2f} Mbps"
            )
            
            # Save checkpoint every 10 MB
            if update.bytes_transferred - last_checkpoint_bytes >= 10 * 1024 * 1024:
                _save_checkpoint(checkpoint_file, controller, update)
                last_checkpoint_bytes = update.bytes_transferred
                logger.info(f"Checkpoint saved at {progress_pct:.1f}%")
        
        controller.set_progress_callback(on_progress)
        
        # Run transfer
        logger.info("Starting resumable transfer...")
        logger.info(f"Checkpoints will be saved to: {checkpoint_file}")
        
        result = await controller.run_transfer(controller.send())
        
        if result:
            logger.info("✓ Transfer completed successfully!")
            # Clean up checkpoint file
            checkpoint_file.unlink(missing_ok=True)
        else:
            logger.error("✗ Transfer interrupted")
            logger.info(f"Checkpoint saved to: {checkpoint_file}")
            logger.info("You can resume this transfer using: hybridlink resume-transfer")
        
        return result
        
    finally:
        test_file.unlink(missing_ok=True)


def _save_checkpoint(checkpoint_file: Path, controller: TransferController, update) -> None:
    """Save transfer checkpoint for resumption."""
    checkpoint_data = {
        "transfer_id": update.transfer_id,
        "file_size": update.total_bytes,
        "bytes_transferred": update.bytes_transferred,
        "chunks_complete": update.chunks_completed,
        "total_chunks": update.total_chunks,
        "timestamp": update.elapsed_seconds,
        "chunk_manager_stats": controller.chunk_manager.get_statistics() if controller.chunk_manager else None,
        "channel_stats": controller.channel_manager.get_summary() if controller.channel_manager else None,
    }
    
    checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))


async def example_resume_transfer():
    """Example: Resume a previously interrupted transfer."""
    
    checkpoint_file = Path(".resumable_example.checkpoint")
    
    if not checkpoint_file.exists():
        logger.error(f"Checkpoint file not found: {checkpoint_file}")
        return False
    
    # Load checkpoint
    logger.info(f"Loading checkpoint: {checkpoint_file}")
    checkpoint_data = json.loads(checkpoint_file.read_text())
    
    logger.info("Checkpoint Information:")
    logger.info(f"  Transfer ID: {checkpoint_data['transfer_id']}")
    logger.info(f"  Progress: {checkpoint_data['bytes_transferred']} / {checkpoint_data['file_size']} bytes")
    logger.info(f"  Chunks: {checkpoint_data['chunks_complete']} / {checkpoint_data['total_chunks']}")
    
    # In a real implementation, you would:
    # 1. Reload the chunk manager state from checkpoint
    # 2. Reconnect channels
    # 3. Resume transfer from where it was interrupted
    
    logger.info("Resume transfer implementation goes here")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "resume":
        asyncio.run(example_resume_transfer())
    else:
        asyncio.run(example_resumable_transfer())
