"""
TelemetryProvider: Unified event emitter for HybridLink ecosystem.
Supports WebSocket broadcasting and local event hooks.
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Set
from dataclasses import asdict
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)

class TelemetryEvent:
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.type = event_type
        self.data = data
        self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp
        })

class TelemetryEmitter:
    """
    Central hub for emitting events from the transfer engine.
    """
    def __init__(self, port: int = 9002):
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.loop = asyncio.get_event_loop()
        self._server = None

    async def start(self):
        """Start the WebSocket server."""
        try:
            self._server = await websockets.serve(self._handler, "0.0.0.0", self.port)
            logger.info(f"🚀 Telemetry server started on ws://0.0.0.0:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start telemetry server: {e}")

    async def stop(self):
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Telemetry server stopped")

    async def _handler(self, websocket, path):
        """Handle new WebSocket connections."""
        self.clients.add(websocket)
        logger.info(f"New telemetry subscriber from {websocket.remote_address}")
        try:
            async for message in websocket:
                # Handle incoming messages if needed
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)

    def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all connected clients."""
        event = TelemetryEvent(event_type, data)
        msg = event.to_json()
        
        # Run in thread-safe way if called from another thread
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast(msg), self.loop)

    async def _broadcast(self, message: str):
        if not self.clients:
            return
        
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )

# Global emitter instance
emitter = TelemetryEmitter()
