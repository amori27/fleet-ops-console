"""WebSocket client with exponential backoff reconnection.

Provides a resilient WebSocket client that automatically reconnects
with exponential backoff and jitter when the connection drops.
"""

import asyncio
import logging
import random
from typing import Any, Callable

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class ReconnectingWebSocketClient:
    """WebSocket client with automatic exponential backoff reconnection.

    Connects to a WebSocket endpoint and reconnects automatically
    on disconnection using exponential backoff with jitter.

    Args:
        url: WebSocket server URL (e.g. ws://host/ws/fleet/updates).
        token: JWT authentication token passed as query parameter.
        on_message: Callback invoked with each received message string.
        initial_delay: Initial reconnection delay in seconds.
        max_delay: Maximum reconnection delay in seconds.
        max_retries: Maximum reconnection attempts (None for infinite).
        backoff_factor: Multiplier for exponential backoff.
    """

    def __init__(
        self,
        url: str,
        token: str,
        on_message: Callable[[str], Any] | None = None,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int | None = None,
        backoff_factor: float = 2.0,
    ) -> None:
        self.url = url
        self.token = token
        self.on_message = on_message
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self._ws: websockets.WebSocketClientProtocol | None = None
        self._running = False
        self._retry_count = 0
        self._stop_event = asyncio.Event()

    @property
    def connected(self) -> bool:
        return self._ws is not None and self._ws.open

    async def connect(self) -> None:
        """Start the client with automatic reconnection."""
        self._running = True
        self._stop_event.clear()
        self._retry_count = 0

        while self._running and not self._stop_event.is_set():
            try:
                await self._connect_once()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

            if not self._running or self._stop_event.is_set():
                break

            delay = self._compute_delay()
            if delay is None:
                logger.error("Max retries (%d) reached. Stopping.", self.max_retries)
                break

            logger.info("Reconnecting in %.1fs (attempt %d)...", delay, self._retry_count)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
                break
            except asyncio.TimeoutError:
                pass

    async def _connect_once(self) -> None:
        """Attempt a single WebSocket connection and read messages."""
        ws_url = f"{self.url}?token={self.token}"
        async with websockets.connect(ws_url) as ws:
            self._ws = ws
            self._retry_count = 0
            logger.info("Connected to %s", self.url)

            async for message in ws:
                if self.on_message is not None:
                    result = self.on_message(message)
                    if asyncio.iscoroutine(result):
                        await result

    def _compute_delay(self) -> float | None:
        """Compute the next reconnection delay using exponential backoff with jitter.

        Returns:
            Delay in seconds, or None if max retries exceeded.
        """
        if self.max_retries is not None and self._retry_count >= self.max_retries:
            return None

        self._retry_count += 1
        base_delay = min(
            self.initial_delay * (self.backoff_factor ** (self._retry_count - 1)),
            self.max_delay,
        )
        jitter = random.uniform(0, base_delay * 0.5)
        return base_delay + jitter

    async def send(self, message: str) -> None:
        """Send a message through the WebSocket.

        Args:
            message: Text message to send.

        Raises:
            ConnectionClosed: If the connection is not active.
        """
        if self._ws is None or not self._ws.open:
            raise ConnectionClosed(None, None)
        await self._ws.send(message)

    async def close(self) -> None:
        """Gracefully stop the client and close the connection."""
        self._running = False
        self._stop_event.set()
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
