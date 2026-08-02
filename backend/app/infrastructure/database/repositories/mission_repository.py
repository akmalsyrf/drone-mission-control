from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.domain.entities import Mission
from app.domain.value_objects import MissionStatus, WaypointSpec
from app.infrastructure.database.models import MissionModel, WaypointModel


class MissionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    def _to_domain(self, row: MissionModel) -> Mission:
        waypoints = [
            WaypointSpec(
                sequence=wp.sequence,
                latitude_deg=wp.latitude_deg,
                longitude_deg=wp.longitude_deg,
                altitude_m=wp.altitude_m,
                hold_seconds=wp.hold_seconds,
            )
            for wp in row.waypoints
        ]
        return Mission(
            id=row.id,
            drone_id=row.drone_id,
            name=row.name,
            status=MissionStatus(row.status),
            waypoints=waypoints,
            progress_percent=row.progress_percent,
            created_at=row.created_at,
        )

    async def add(self, mission: Mission) -> Mission:
        async with self._session_factory() as session:
            row = MissionModel(
                id=mission.id,
                drone_id=mission.drone_id,
                name=mission.name,
                status=mission.status.value,
                progress_percent=mission.progress_percent,
            )
            for wp in mission.waypoints:
                row.waypoints.append(
                    WaypointModel(
                        sequence=wp.sequence,
                        latitude_deg=wp.latitude_deg,
                        longitude_deg=wp.longitude_deg,
                        altitude_m=wp.altitude_m,
                        hold_seconds=wp.hold_seconds,
                    )
                )
            session.add(row)
            await session.commit()
            result = await session.execute(
                select(MissionModel)
                .options(selectinload(MissionModel.waypoints))
                .where(MissionModel.id == row.id)
            )
            loaded = result.scalar_one()
            return self._to_domain(loaded)

    async def get(self, mission_id: UUID) -> Mission | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MissionModel)
                .options(selectinload(MissionModel.waypoints))
                .where(MissionModel.id == mission_id)
            )
            row = result.scalar_one_or_none()
            return self._to_domain(row) if row else None

    async def list_for_drone(self, drone_id: UUID) -> list[Mission]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MissionModel)
                .options(selectinload(MissionModel.waypoints))
                .where(MissionModel.drone_id == drone_id)
                .order_by(MissionModel.created_at.desc())
            )
            return [self._to_domain(r) for r in result.scalars().all()]

    async def save(self, mission: Mission) -> Mission:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MissionModel)
                .options(selectinload(MissionModel.waypoints))
                .where(MissionModel.id == mission.id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                raise KeyError(f"Mission {mission.id} not found")
            row.name = mission.name
            row.status = mission.status.value
            row.progress_percent = mission.progress_percent
            await session.commit()
            return await self.get(mission.id)  # type: ignore[return-value]
