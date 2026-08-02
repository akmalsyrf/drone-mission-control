from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.entities import Drone
from app.domain.value_objects import AdapterType, ConnectionStatus
from app.infrastructure.database.models import DroneModel


class DroneRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    def _to_domain(self, row: DroneModel) -> Drone:
        return Drone(
            id=row.id,
            name=row.name,
            adapter_type=AdapterType(row.adapter_type),
            connection_uri=row.connection_uri,
            connection_status=ConnectionStatus(row.connection_status),
            last_heartbeat=row.last_heartbeat,
            current_mission_id=row.current_mission_id,
            metadata=dict(row.metadata_json or {}),
        )

    def _apply(self, row: DroneModel, drone: Drone) -> None:
        row.name = drone.name
        row.adapter_type = drone.adapter_type.value
        row.connection_uri = drone.connection_uri
        row.connection_status = drone.connection_status.value
        row.last_heartbeat = drone.last_heartbeat
        row.current_mission_id = drone.current_mission_id
        row.metadata_json = dict(drone.metadata)

    async def add(self, drone: Drone) -> Drone:
        async with self._session_factory() as session:
            row = DroneModel(
                id=drone.id,
                name=drone.name,
                adapter_type=drone.adapter_type.value,
                connection_uri=drone.connection_uri,
                connection_status=drone.connection_status.value,
                last_heartbeat=drone.last_heartbeat,
                current_mission_id=drone.current_mission_id,
                metadata_json=dict(drone.metadata),
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._to_domain(row)

    async def get(self, drone_id: UUID) -> Drone | None:
        async with self._session_factory() as session:
            row = await session.get(DroneModel, drone_id)
            return self._to_domain(row) if row else None

    async def list_all(self) -> list[Drone]:
        async with self._session_factory() as session:
            result = await session.execute(select(DroneModel).order_by(DroneModel.name))
            return [self._to_domain(r) for r in result.scalars().all()]

    async def save(self, drone: Drone) -> Drone:
        async with self._session_factory() as session:
            row = await session.get(DroneModel, drone.id)
            if row is None:
                raise KeyError(f"Drone {drone.id} not found")
            self._apply(row, drone)
            await session.commit()
            await session.refresh(row)
            return self._to_domain(row)

    async def delete(self, drone_id: UUID) -> None:
        async with self._session_factory() as session:
            row = await session.get(DroneModel, drone_id)
            if row is None:
                return
            await session.delete(row)
            await session.commit()
