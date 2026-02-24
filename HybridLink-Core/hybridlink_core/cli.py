"""
CLI: Command-line interface for HybridLink-Core transfer engine.
"""

import logging
import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.live import Live
from colorama import init

from hybridlink_core import __version__
from hybridlink_core.transfer_controller import TransferController
from hybridlink_core.models import TransferConfig, ProgressUpdate
from hybridlink_core.config import get_config_dir

# Initialize colorama for Windows compatibility
init(autoreset=True)

# Rich console for nice output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(__version__)
def cli():
    """HybridLink-Core: Cross-platform multipath file transfer engine."""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--host",
    default="192.168.1.100",
    help="Destination Android device IP or hostname (WiFi)",
)
@click.option("--chunk-size", default=4 * 1024 * 1024, help="Chunk size in bytes")
@click.option("--usb", is_flag=True, default=True, help="Enable USB transfer (default)")
@click.option("--no-usb", is_flag=True, help="Disable USB transfer")
@click.option("--wifi", is_flag=True, default=True, help="Enable WiFi transfer (default)")
@click.option("--no-wifi", is_flag=True, help="Disable WiFi transfer")
@click.option("--verify", is_flag=True, default=True, help="Verify integrity (default)")
@click.option("--no-verify", is_flag=True, help="Skip integrity verification")
def send(file_path, host, chunk_size, usb, no_usb, wifi, no_wifi, verify, no_verify):
    """Send a file to Android device over USB and/or WiFi."""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            console.print("[red]Error: File not found[/red]")
            return

        # Configure transfer
        config = TransferConfig(
            chunk_size=chunk_size,
            usb_enabled=(usb and not no_usb),
            wifi_enabled=(wifi and not no_wifi),
            verify_integrity=(verify and not no_verify),
        )

        console.print(f"[cyan]HybridLink-Core v{__version__}[/cyan]")
        console.print(f"[yellow]Sending: {file_path.name}[/yellow]")
        console.print(f"[cyan]Destination: {host}[/cyan]")
        console.print(f"[cyan]File size: {_format_size(file_path.stat().st_size)}[/cyan]")

        # Run transfer
        result = asyncio.run(_run_send(file_path, host, config))

        if result:
            console.print("[green]✓ Transfer completed successfully[/green]")
        else:
            console.print("[red]✗ Transfer failed[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Transfer interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument("destination", type=click.Path())
@click.option("--file-size", required=True, type=int, help="Size of file to receive (bytes)")
@click.option("--chunk-size", default=4 * 1024 * 1024, help="Chunk size in bytes")
@click.option("--usb", is_flag=True, default=True, help="Enable USB transfer (default)")
@click.option("--no-usb", is_flag=True, help="Disable USB transfer")
@click.option("--wifi", is_flag=True, default=True, help="Enable WiFi transfer (default)")
@click.option("--no-wifi", is_flag=True, help="Disable WiFi transfer")
@click.option("--verify", is_flag=True, default=True, help="Verify integrity (default)")
@click.option("--no-verify", is_flag=True, help="Skip integrity verification")
def receive(destination, file_size, chunk_size, usb, no_usb, wifi, no_wifi, verify, no_verify):
    """Receive a file from Android device over USB and/or WiFi."""
    try:
        destination = Path(destination)

        # Create destination directory if needed
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Configure transfer
        config = TransferConfig(
            chunk_size=chunk_size,
            usb_enabled=(usb and not no_usb),
            wifi_enabled=(wifi and not no_wifi),
            verify_integrity=(verify and not no_verify),
        )

        console.print(f"[cyan]HybridLink-Core v{__version__}[/cyan]")
        console.print(f"[yellow]Receiving to: {destination}[/yellow]")
        console.print(f"[cyan]File size: {_format_size(file_size)}[/cyan]")

        # Run transfer
        result = asyncio.run(_run_receive(destination, file_size, config))

        if result:
            console.print("[green]✓ Transfer completed successfully[/green]")
        else:
            console.print("[red]✗ Transfer failed[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Transfer interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def configure():
    """Configure HybridLink-Core settings."""
    config_dir = get_config_dir()

    console.print(f"[cyan]Configuration Directory: {config_dir}[/cyan]")

    # Display current configuration
    table = Table(title="HybridLink-Core Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Config Directory", str(config_dir))
    table.add_row("Version", __version__)
    table.add_row("Default Chunk Size", "4 MB")
    table.add_row("USB Port (ADB)", "9000")
    table.add_row("WiFi Port", "9001")

    console.print(table)


@cli.command()
def status():
    """Show status of HybridLink-Core installation."""
    console.print(f"[cyan]HybridLink-Core v{__version__}[/cyan]")

    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    # Check Python version
    import sys

    table.add_row("Python Version", f"{sys.version.split()[0]}")

    # Check required packages
    try:
        import paramiko

        table.add_row("Paramiko", "✓ Installed")
    except ImportError:
        table.add_row("Paramiko", "[red]✗ Missing[/red]")

    try:
        import pydantic

        table.add_row("Pydantic", "✓ Installed")
    except ImportError:
        table.add_row("Pydantic", "[red]✗ Missing[/red]")

    try:
        import click

        table.add_row("Click", "✓ Installed")
    except ImportError:
        table.add_row("Click", "[red]✗ Missing[/red]")

    try:
        import rich

        table.add_row("Rich", "✓ Installed")
    except ImportError:
        table.add_row("Rich", "[red]✗ Missing[/red]")

    console.print(table)


async def _run_send(
    file_path: Path, destination_host: str, config: TransferConfig
) -> bool:
    """Execute send transfer."""
    controller = TransferController(config)

    # Initialize sender
    if not await controller.initialize_sender(file_path, destination_host):
        return False

    # Connect channels
    if not await controller.connect_channels():
        return False

    # Setup progress display
    _setup_progress_display(controller)

    # Run transfer
    return await controller.run_transfer(controller.send())


async def _run_receive(
    destination: Path, file_size: int, config: TransferConfig
) -> bool:
    """Execute receive transfer."""
    controller = TransferController(config)

    # Initialize receiver
    if not await controller.initialize_receiver(destination, file_size):
        return False

    # Connect channels
    if not await controller.connect_channels():
        return False

    # Setup progress display
    _setup_progress_display(controller)

    # Run transfer
    return await controller.run_transfer(controller.receive())


def _setup_progress_display(controller: TransferController) -> None:
    """Setup real-time progress display."""

    def progress_callback(update: ProgressUpdate) -> None:
        if update.state == "transferring":
            # Get current progress
            percent = update.progress_percent
            speed = update.current_speed_mbps

            # Display progress bar with format
            progress_text = (
                f"[cyan]{percent:6.1f}%[/cyan] "
                f"[green]{_format_size(update.bytes_transferred)}[/green] / "
                f"[yellow]{_format_size(update.total_bytes)}[/yellow] "
                f"[magenta]{speed:.2f} Mbps[/magenta]"
            )

            # Add ETA if available
            if update.eta_seconds is not None:
                eta_text = _format_time(update.eta_seconds)
                progress_text += f" [cyan]ETA: {eta_text}[/cyan]"

            # Channel status
            if update.channels:
                channel_info = " | ".join(
                    f"{name}: {stats.transfer_speed_mbps:.1f} Mbps"
                    for name, stats in update.channels.items()
                    if stats and stats.available
                )
                if channel_info:
                    progress_text += f"\n[dim]{channel_info}[/dim]"

            console.print(progress_text, end="\r")

    controller.set_progress_callback(progress_callback)


def _format_size(size: int) -> str:
    """Format size as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def _format_time(seconds: int) -> str:
    """Format time duration as human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
