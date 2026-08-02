"""In-process telemetry hub — fan-out to WS/Redis/MQTT handlers."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from uuid import UUID

from app.config.logging import get_logger
from app.domain.entities import TelemetrySnapshot
from app.domain.interfaces import TelemetryBroadcasterPort, TelemetryHandler

logger = get_logger(__name__)


class TelemetryHub:
    def __init__(self) -> None:
        self._subscribers: dict[UUID, list[asyncio.Queue[TelemetrySnapshot]]] = {}
        self._wildcard: list[asyncio.Queue[TelemetrySnapshot]] = []
        self._handlers: list[TelemetryHandler] = []
        self._broadcasters: list[TelemetryBroadcasterPort] = []
        self._lock = asyncio.Lock()

    def add_handler(self, handler: TelemetryHandler) -> None:
        self._handlers.append(handler)

    def add_broadcaster(self, broadcaster: TelemetryBroadcasterPort) -> None:
        self._broadcasters.append(broadcaster)

    async def publish(self, telemetry: TelemetrySnapshot) -> None:
        for handler in self._handlers:
            try:
                await handler(telemetry)
            except Exception:
                logger.exception("telemetry_handler_failed", drone_id=str(telemetry.drone_id))
        for broadcaster in self._broadcasters:
            try:
                await broadcaster.publish(telemetry)
            except Exception:
                logger.exception("telemetry_broadcaster_failed", drone_id=str(telemetry.drone_id))
        async with self._lock:
            queues = list(self._subscribers.get(telemetry.drone_id, []))
            queues.extend(self._wildcard)
        for queue in queues:
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(telemetry)

    async def subscribe(
        self,
        drone_id: UUID | None = None,
        *,
        maxsize: int = 64,
    ) -> AsyncIterator[TelemetrySnapshot]:
        queue: asyncio.Queue[TelemetrySnapshot] = asyncio.Queue(maxsize=maxsize)
        async with self._lock:
            if drone_id is None:
                self._wildcard.append(queue)
            else:
                self._subscribers.setdefault(drone_id, []).append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                if drone_id is None:
                    with suppress(ValueError):
                        self._wildcard.remove(queue)
                else:
                    queues = self._subscribers.get(drone_id, [])
                    with suppress(ValueError):
                        queues.remove(queue)
                    if not queues:
                        self._subscribers.pop(drone_id, None)
