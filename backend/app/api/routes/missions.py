from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.schemas import MissionCreateRequest, MissionResponse, WaypointBody
from app.application.services.fleet_service import DroneNotFoundError
from app.application.services.mission_service import MissionNotFoundError, MissionService
from app.auth.dependencies import AuthPrincipal, require_auth
from app.domain.entities import Mission
from app.domain.value_objects import WaypointSpec

router = APIRouter(prefix="/drones/{drone_id}/missions", tags=["missions"])


def get_mission_service(request: Request) -> MissionService:
    service: MissionService = request.app.state.container.mission_service
    return service


def _to_response(mission: Mission) -> MissionResponse:
    return MissionResponse(
        id=mission.id,
        drone_id=mission.drone_id,
        name=mission.name,
        status=mission.status.value,
        progress_percent=mission.progress_percent,
        waypoints=[
            WaypointBody(
                sequence=wp.sequence,
                latitude_deg=wp.latitude_deg,
                longitude_deg=wp.longitude_deg,
                altitude_m=wp.altitude_m,
                hold_seconds=wp.hold_seconds,
            )
            for wp in mission.waypoints
        ],
        created_at=mission.created_at,
    )


@router.get("", response_model=list[MissionResponse])
async def list_missions(
    drone_id: UUID,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[MissionService, Depends(get_mission_service)],
) -> list[MissionResponse]:
    try:
        missions = await service.list_missions(drone_id)
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [_to_response(m) for m in missions]


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(
    drone_id: UUID,
    body: MissionCreateRequest,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[MissionService, Depends(get_mission_service)],
) -> MissionResponse:
    waypoints = [
        WaypointSpec(
            sequence=wp.sequence,
            latitude_deg=wp.latitude_deg,
            longitude_deg=wp.longitude_deg,
            altitude_m=wp.altitude_m,
            hold_seconds=wp.hold_seconds,
        )
        for wp in body.waypoints
    ]
    try:
        mission = await service.create_mission(drone_id, body.name, waypoints)
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(mission)


@router.post("/{mission_id}/start", response_model=MissionResponse)
async def start_mission(
    drone_id: UUID,
    mission_id: UUID,
    _principal: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[MissionService, Depends(get_mission_service)],
) -> MissionResponse:
    _ = (drone_id, _principal)
    try:
        mission = await service.upload_and_start(mission_id)
    except (MissionNotFoundError, DroneNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(mission)
