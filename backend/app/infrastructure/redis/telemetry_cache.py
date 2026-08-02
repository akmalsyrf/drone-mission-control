from __future__ import annotations

from uuid import UUID

import redis.asyncio as redis

from app.config.logging import get_logger
from app.config.settings import Settings
from app.domain.entities import TelemetrySnapshot

logger = get_logger(__name__)


class RedisTelemetryCache:
    def __init__(self, client: redis.Redis, settings: Settings) -> None:
        self._client = client
        self._ttl = settings.redis_telemetry_ttl_seconds
        self._channel = settings.redis_telemetry_channel

    def _key(self, drone_id: UUID) -> str:
        return f"dmc:telemetry:latest:{drone_id}"

    async def set_latest(self, telemetry: TelemetrySnapshot) -> None:
        payload = telemetry.model_dump_json()
        await self._client.set(self._key(telemetry.drone_id), payload, ex=self._ttl)

    async def get_latest(self, drone_id: UUID) -> TelemetrySnapshot | None:
        raw = await self._client.get(self._key(drone_id))
        if raw is None:
            return None
        text = raw.decode() if isinstance(raw, bytes) else str(raw)
        return TelemetrySnapshot.model_validate_json(text)


class RedisTelemetryBroadcaster:
    def __init__(self, client: redis.Redis, settings: Settings) -> None:
        self._client = client
        self._channel = settings.redis_telemetry_channel

    async def publish(self, telemetry: TelemetrySnapshot) -> None:
        await self._client.publish(self._channel, telemetry.model_dump_json())
        logger.debug("redis_telemetry_published", drone_id=str(telemetry.drone_id))
