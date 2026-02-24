"""
Example: Simple TCP Server for receiving chunks.

This demonstrates how to set up a receiver endpoint.
"""

import asyncio
import logging
from pathlib import Path

from hybridlink_core import ChunkManager
from hybridlink_core.transfer_controller import TransferController
from hybridlink_core.models import TransferConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def example_receiver():
    """Example: Receive a file using HybridLink-Core."""
    
    # Configuration
    destination = Path("received_file.bin")
    file_size = 100 * 1024 * 1024  # 100 MB
    
    config = TransferConfig(
        chunk_size=4 * 1024 * 1024,  # 4 MB chunks
        usb_enabled=True,
        wifi_enabled=True,
        verify_integrity=True,
    )
    
    # Create controller
    controller = TransferController(config)
    
    # Initialize receiver
    logger.info(f"Initializing receiver for: {destination}")
    success = await controller.initialize_receiver(
        destination_path=destination,
        file_size=file_size,
        transfer_id="example_transfer",
    )
    
    if not success:
        logger.error("Failed to initialize receiver")
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
    logger.info("Starting receive transfer...")
    result = await controller.run_transfer(controller.receive())
    
    if result:
        logger.info("✓ Transfer completed successfully!")
    else:
        logger.error("✗ Transfer failed!")
    
    return result


if __name__ == "__main__":
    asyncio.run(example_receiver())
