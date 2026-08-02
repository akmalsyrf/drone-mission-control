from __future__ import annotations

import asyncio
from contextlib import suppress

import aiomqtt

from app.config.logging import get_logger
from app.config.settings import Settings
from app.domain.entities import TelemetrySnapshot

logger = get_logger(__name__)


class MqttTelemetryPublisher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: aiomqtt.Client | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if not self._settings.mqtt_enabled:
            logger.info("mqtt_disabled")
            return
        self._client = aiomqtt.Client(
            hostname=self._settings.mqtt_host,
            port=self._settings.mqtt_port,
        )
        await self._client.__aenter__()
        logger.info("mqtt_connected", host=self._settings.mqtt_host)

    async def disconnect(self) -> None:
        if self._client is None:
            return
        with suppress(Exception):
            await self._client.__aexit__(None, None, None)
        self._client = None

    async def publish(self, telemetry: TelemetrySnapshot) -> None:
        if not self._settings.mqtt_enabled or self._client is None:
            return
        topic = f"{self._settings.mqtt_topic_prefix}/{telemetry.drone_id}"
        async with self._lock:
            await self._client.publish(topic, telemetry.model_dump_json(), qos=0)
