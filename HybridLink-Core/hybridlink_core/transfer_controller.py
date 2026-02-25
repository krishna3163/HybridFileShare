"""
TransferController: Orchestrates multipath file transfers (send and receive modes).
"""

import logging
import asyncio
import signal
from pathlib import Path
from typing import Optional, List, Awaitable
from enum import Enum

from hybridlink_core.models import TransferConfig, TransferMetadata, ProgressUpdate
from hybridlink_core.chunk_manager import ChunkManager
from hybridlink_core.channel_manager import ChannelManager
from hybridlink_core.multichannel_scheduler import MultiChannelScheduler
from hybridlink_core.usb_transport import UsbTransport, TransportConfig
from hybridlink_core.wifi_transport import WifiTransport
from hybridlink_core.chunk_assembler import ChunkAssembler
from hybridlink_core.integrity_verifier import IntegrityVerifier
from hybridlink_core.security_manager import SecurityManager
from hybridlink_core.progress_reporter import ProgressReporter
from hybridlink_core.config import TransferMode, TransferState, METADATA_FILE
from pathlib import Path

logger = logging.getLogger(__name__)


class TransferController:
    """
    Main controller for orchestrating multipath file transfers.
    
    Supports:
    - Sending files over USB and WiFi simultaneously
    - Receiving files with chunk assembly
    - Resume interrupted transfers
    - Progress tracking and reporting
    - Graceful shutdown with cleanup
    """

    def __init__(self, config: Optional[TransferConfig] = None):
        """
        Initialize TransferController.
        
        Args:
            config: Transfer configuration
        """
        self.config = config or TransferConfig()
        self.mode: Optional[TransferMode] = None
        self.state = TransferState.IDLE

        # Core components
        self.chunk_manager: Optional[ChunkManager] = None
        self.channel_manager: Optional[ChannelManager] = None
        self.scheduler: Optional[MultiChannelScheduler] = None
        self.progress_reporter: Optional[ProgressReporter] = None
        self.chunk_assembler: Optional[ChunkAssembler] = None
        self.security_manager = SecurityManager()

        # Transfer metadata
        self.metadata: Optional[TransferMetadata] = None
        self.metadata_file: Optional[Path] = None

        # State management
        self._shutdown_event = asyncio.Event()
        self._transfer_task: Optional[asyncio.Task] = None

        logger.info("TransferController initialized")

    def set_progress_callback(
        self,
        callback,
    ) -> None:
        """
        Set a callback for progress updates.
        
        Args:
            callback: Callable accepting ProgressUpdate
        """
        if self.progress_reporter:
            self.progress_reporter.add_callback(callback)

    async def initialize_sender(
        self,
        file_path: Path,
        destination_host: str,
        transfer_id: str = "",
    ) -> bool:
        """
        Initialize sender mode (send file over multipath).
        
        Args:
            file_path: Path to file to send
            destination_host: Destination WiFi host
            transfer_id: Optional transfer ID
            
        Returns:
            True if initialization successful
        """
        try:
            self.mode = TransferMode.SEND
            self.state = TransferState.PREPARING

            # Initialize ChunkManager
            self.chunk_manager = ChunkManager(self.config.chunk_size)
            self.chunk_manager.initialize_file(file_path, transfer_id)

            # Initialize ChannelManager with transports
            self.channel_manager = ChannelManager()

            if self.config.usb_enabled:
                usb_transport = UsbTransport(
                    host=self.config.usb_host,
                    port=self.config.usb_port,
                    config=TransportConfig(timeout=self.config.channel_timeout),
                )
                self.channel_manager.register_channel("usb", usb_transport)

            if self.config.wifi_enabled:
                wifi_transport = WifiTransport(
                    host=destination_host,
                    port=self.config.wifi_port,
                    config=TransportConfig(timeout=self.config.channel_timeout),
                )
                self.channel_manager.register_channel("wifi", wifi_transport)

            # Initialize ProgressReporter
            file_size = file_path.stat().st_size
            self.progress_reporter = ProgressReporter(
                transfer_id=self.chunk_manager.transfer_id,
                total_bytes=file_size,
                chunk_manager=self.chunk_manager,
                channel_manager=self.channel_manager,
            )

            # Initialize Scheduler
            self.scheduler = MultiChannelScheduler(
                self.chunk_manager, self.channel_manager, self.config.max_retries
            )
            await self.scheduler.initialize()

            # Create metadata checkp int
            self.metadata_file = Path.home() / f".hybridlink_{self.chunk_manager.transfer_id}.checkpoint"

            logger.info(f"Sender initialized for: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error initializing sender: {e}")
            self.state = TransferState.FAILED
            return False

    async def initialize_receiver(
        self,
        destination_path: Path,
        file_size: int,
        transfer_id: str = "",
    ) -> bool:
        """
        Initialize receiver mode (receive file over multipath).
        
        Args:
            destination_path: Path where received file will be saved
            file_size: Total size of file being received
            transfer_id: Optional transfer ID
            
        Returns:
            True if initialization successful
        """
        try:
            self.mode = TransferMode.RECEIVE
            self.state = TransferState.PREPARING

            # Initialize ChunkManager
            self.chunk_manager = ChunkManager(self.config.chunk_size)
            self.chunk_manager.file_size = file_size
            self.chunk_manager._create_chunks()
            self.chunk_manager.transfer_id = transfer_id or "recv_" + Path(destination_path).stem

            # Initialize ChannelManager
            self.channel_manager = ChannelManager()

            if self.config.usb_enabled:
                usb_transport = UsbTransport(
                    config=TransportConfig(timeout=self.config.channel_timeout),
                )
                self.channel_manager.register_channel("usb", usb_transport)

            if self.config.wifi_enabled:
                wifi_transport = WifiTransport(
                    host="0.0.0.0",  # Listen on all interfaces
                    config=TransportConfig(timeout=self.config.channel_timeout),
                )
                self.channel_manager.register_channel("wifi", wifi_transport)

            # Initialize ChunkAssembler
            self.chunk_assembler = ChunkAssembler(
                destination_path, file_size, self.config.chunk_size
            )

            # Initialize ProgressReporter
            self.progress_reporter = ProgressReporter(
                transfer_id=self.chunk_manager.transfer_id,
                total_bytes=file_size,
                chunk_manager=self.chunk_manager,
                channel_manager=self.channel_manager,
            )

            # Initialize Scheduler
            self.scheduler = MultiChannelScheduler(
                self.chunk_manager, self.channel_manager, self.config.max_retries
            )
            await self.scheduler.initialize()

            # Create metadata checkp int
            self.metadata_file = Path.home() / f".hybridlink_{self.chunk_manager.transfer_id}.checkpoint"

            logger.info(f"Receiver initialized for: {destination_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error initializing receiver: {e}")
            self.state = TransferState.FAILED
            return False

    async def connect_channels(self) -> bool:
        """
        Connect all available channels.
        
        Returns:
            True if at least one channel connected
        """
        if not self.channel_manager:
            return False

        try:
            channels_to_connect = list(self.channel_manager.channels.keys())

            for channel_type in channels_to_connect:
                connected = await self.channel_manager.connect_channel(channel_type)
                if not connected:
                    logger.warning(f"Failed to connect {channel_type} channel")

            available = await self.channel_manager.get_available_channels()

            if not available:
                logger.error("No channels connected")
                self.state = TransferState.FAILED
                return False

            logger.info(f"Connected channels: {', '.join(available)}")
            return True

        except Exception as e:
            logger.error(f"Error connecting channels: {e}")
            self.state = TransferState.FAILED
            return False

    async def send(self) -> bool:
        """
        Execute send transfer.
        
        Returns:
            True if transfer successful
        """
        if self.mode != TransferMode.SEND or not self.scheduler:
            logger.error("Not in sender mode or scheduler not initialized")
            return False

        try:
            self.state = TransferState.TRANSFERRING
            pending = self.chunk_manager.get_pending_chunks()

            while pending and not self._shutdown_event.is_set():
                # Schedule transfers
                schedule = await self.scheduler.schedule_transfers(concurrent_transfers=2)

                for channel_type, requests in schedule.items():
                    for request in requests:
                        try:
                            # Get chunk data
                            chunk_data = self.chunk_manager.get_chunk_data(request.chunk_id)

                            # Send via channel
                            transport = self.channel_manager.channels[channel_type]
                            success, bytes_sent = await transport.send_chunk(
                                chunk_data, request.chunk_id
                            )

                            if success:
                                await self.scheduler.handle_chunk_success(
                                    request.chunk_id, bytes_sent, channel_type
                                )

                                # Update progress
                                bytes_transferred = self.chunk_manager.get_bytes_transferred()
                                self.progress_reporter.update_progress(bytes_transferred)
                            else:
                                await self.scheduler.handle_chunk_failure(
                                    request.chunk_id,
                                    channel_type,
                                    error="Send failed",
                                )

                        except Exception as e:
                            await self.scheduler.handle_chunk_failure(
                                request.chunk_id, channel_type, error=str(e)
                            )

                # Check for pending chunks
                pending = self.chunk_manager.get_pending_chunks()

                if pending and not self._shutdown_event.is_set():
                    await asyncio.sleep(0.1)

            # Check if all chunks transferred
            transferred, total = self.chunk_manager.get_transfer_progress()

            if transferred == total:
                self.state = TransferState.COMPLETED
                logger.info("Transfer completed successfully")
                self.progress_reporter.print_summary()
                return True
            else:
                self.state = TransferState.FAILED
                failed = self.scheduler.get_failed_chunks()
                logger.error(f"Transfer failed - {len(failed)} chunks could not be transferred")
                return False

        except Exception as e:
            logger.error(f"Error in send: {e}")
            self.state = TransferState.FAILED
            return False

    async def receive(self) -> bool:
        """
        Execute receive transfer.
        
        Returns:
            True if transfer successful and file assembled
        """
        if self.mode != TransferMode.RECEIVE or not self.chunk_assembler:
            logger.error("Not in receiver mode or assembler not initialized")
            return False

        try:
            self.state = TransferState.TRANSFERRING

            # Listen on channels for incoming chunks
            pending = self.chunk_manager.get_pending_chunks()

            while pending and not self._shutdown_event.is_set():
                for channel_type in await self.channel_manager.get_available_channels():
                    try:
                        transport = self.channel_manager.channels[channel_type]

                        # Try to receive chunk (non-blocking)
                        chunk_data = await asyncio.wait_for(
                            transport.receive_chunk(), timeout=1.0
                        )

                        if chunk_data:
                            # Determine chunk_id from first 4 bytes of incoming data
                            # (implementation depends on protocol)
                            received, total = self.chunk_assembler.get_assembly_progress()

                            if received < total:
                                # Write chunk
                                chunk_id = received
                                success = self.chunk_assembler.write_chunk(
                                    chunk_id, chunk_data
                                )

                                if success:
                                    self.channel_manager.record_transfer(
                                        channel_type, len(chunk_data)
                                    )
                                    self.chunk_manager.mark_transferred(chunk_id)

                                    # Update progress
                                    bytes_transferred = (
                                        received * self.config.chunk_size
                                    )
                                    self.progress_reporter.update_progress(
                                        bytes_transferred
                                    )

                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.debug(f"Error receiving on {channel_type}: {e}")

                pending = self.chunk_manager.get_pending_chunks()

                if pending and not self._shutdown_event.is_set():
                    await asyncio.sleep(0.1)

            # Try to assemble file
            received, total = self.chunk_assembler.get_assembly_progress()

            if received == total:
                logger.info("All chunks received, assembling file...")

                if self.chunk_assembler.assemble_file(
                    verify_final=self.config.verify_integrity
                ):
                    self.state = TransferState.COMPLETED
                    logger.info("Transfer completed and verified successfully")
                    self.progress_reporter.print_summary()
                    return True
                else:
                    self.state = TransferState.FAILED
                    logger.error("File assembly failed")
                    return False
            else:
                self.state = TransferState.FAILED
                logger.error(f"Transfer incomplete - {total - received} chunks not received")
                return False

        except Exception as e:
            logger.error(f"Error in receive: {e}")
            self.state = TransferState.FAILED
            return False

    async def shutdown(self) -> None:
        """Gracefully shutdown the transfer."""
        logger.info("Shutdown initiated...")
        self._shutdown_event.set()

        # Cancel transfer task if running
        if self._transfer_task and not self._transfer_task.done():
            self._transfer_task.cancel()
            try:
                await self._transfer_task
            except asyncio.CancelledError:
                pass

        # Disconnect channels
        if self.channel_manager:
            await self.channel_manager.disconnect_all()

        # Cleanup
        if self.chunk_assembler:
            self.chunk_assembler.cleanup()

        # Clean up metadata checkpoint
        if self.metadata_file and self.metadata_file.exists():
            self.metadata_file.unlink()

        self.state = TransferState.IDLE
        logger.info("Shutdown complete")

    async def run_transfer(self, transfer_coro: Awaitable) -> bool:
        """
        Run a transfer operation with signal handling.
        
        Args:
            transfer_coro: Coroutine for send() or receive()
            
        Returns:
            True if transfer successful
        """
        try:
            # Setup signal handlers for graceful shutdown
            loop = asyncio.get_event_loop()

            def handle_signal(sig):
                logger.info(f"Received signal {sig}, initiating graceful shutdown...")
                asyncio.create_task(self.shutdown())

            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, handle_signal, sig)

            # Run transfer
            result = await transfer_coro
            return result

        except asyncio.CancelledError:
            logger.info("Transfer cancelled")
            return False
        except Exception as e:
            logger.error(f"Error running transfer: {e}")
            return False
        finally:
            await self.shutdown()

    def get_status(self) -> dict:
        """Get current transfer status."""
        return {
            "state": self.state.value if self.state else "unknown",
            "mode": self.mode.value if self.mode else None,
            "chunk_manager": self.chunk_manager.get_statistics() if self.chunk_manager else None,
            "progress": self.progress_reporter.get_status()
            if self.progress_reporter
            else None,
            "channels": self.channel_manager.get_summary()
            if self.channel_manager
            else None,
        }
