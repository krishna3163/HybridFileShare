"""
Example: Simple TCP Client for sending chunks.

This demonstrates how to set up a sender endpoint.
"""

import asyncio
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

from hybridlink_core import ChunkManager
from hybridlink_core.transfer_controller import TransferController
from hybridlink_core.models import TransferConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def example_sender():
    """Example: Send a file using HybridLink-Core."""
    
    # Create a test file (100 MB)
    logger.info("Creating test file (100 MB)...")
    with NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        test_file = Path(tmp.name)
        # Write 100 MB of test data
        chunk_size = 1024 * 1024  # 1 MB
        for i in range(100):
            tmp.write(b"X" * chunk_size)
    
    try:
        # Configuration
        destination_host = "192.168.1.100"  # Android device IP
        
        config = TransferConfig(
            chunk_size=4 * 1024 * 1024,  # 4 MB chunks
            usb_enabled=True,
            wifi_enabled=True,
            verify_integrity=True,
        )
        
        # Create controller
        controller = TransferController(config)
        
        # Initialize sender
        logger.info(f"Initializing sender for: {test_file.name}")
        success = await controller.initialize_sender(
            file_path=test_file,
            destination_host=destination_host,
            transfer_id="example_transfer",
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
        
        # Setup progress callback
        def on_progress(update):
            progress_pct = (update.bytes_transferred / update.total_bytes) * 100
            logger.info(
                f"Progress: {progress_pct:.1f}% "
                f"({update.bytes_transferred} / {update.total_bytes} bytes) "
                f"Speed: {update.current_speed_mbps:.2f} Mbps"
            )
        
        controller.set_progress_callback(on_progress)
        
        # Run transfer
        logger.info("Starting send transfer...")
        result = await controller.run_transfer(controller.send())
        
        if result:
            logger.info("✓ Transfer completed successfully!")
        else:
            logger.error("✗ Transfer failed!")
        
        return result
        
    finally:
        # Clean up test file
        test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(example_sender())
