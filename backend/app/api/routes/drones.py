from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.schemas import CommandBody, DroneCreateRequest, DroneResponse, TelemetryResponse
from app.application.services.fleet_service import (
    DroneAlreadyExistsError,
    DroneNotFoundError,
    FleetService,
)
from app.auth.dependencies import AuthPrincipal, require_auth
from app.domain.entities import Drone

router = APIRouter(prefix="/drones", tags=["drones"])


def get_fleet_service(request: Request) -> FleetService:
    service: FleetService = request.app.state.container.fleet_service
    return service


def _to_response(drone: Drone) -> DroneResponse:
    return DroneResponse(
        id=drone.id,
        name=drone.name,
        adapter_type=drone.adapter_type,
        connection_uri=drone.connection_uri,
        connection_status=drone.connection_status,
        last_heartbeat=drone.last_heartbeat,
        current_mission_id=drone.current_mission_id,
        metadata=drone.metadata,
    )


@router.get("", response_model=list[DroneResponse])
async def list_drones(
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> list[DroneResponse]:
    return [_to_response(d) for d in await service.list_drones()]


@router.post("", response_model=DroneResponse, status_code=status.HTTP_201_CREATED)
async def register_drone(
    body: DroneCreateRequest,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> DroneResponse:
    try:
        drone = await service.register_drone(
            name=body.name,
            adapter_type=body.adapter_type,
            connection_uri=body.connection_uri,
            metadata=body.metadata,
            auto_connect=body.auto_connect,
        )
    except DroneAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_response(drone)


@router.get("/{drone_id}", response_model=DroneResponse)
async def get_drone(
    drone_id: UUID,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> DroneResponse:
    try:
        return _to_response(await service.get_drone(drone_id))
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{drone_id}/connect", response_model=DroneResponse)
async def connect_drone(
    drone_id: UUID,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> DroneResponse:
    try:
        return _to_response(await service.connect_drone(drone_id))
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{drone_id}/disconnect", response_model=DroneResponse)
async def disconnect_drone(
    drone_id: UUID,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> DroneResponse:
    try:
        return _to_response(await service.disconnect_drone(drone_id))
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{drone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drone(
    drone_id: UUID,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> None:
    try:
        await service.delete_drone(drone_id)
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{drone_id}/commands", status_code=status.HTTP_202_ACCEPTED)
async def send_command(
    drone_id: UUID,
    body: CommandBody,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> dict[str, str]:
    try:
        await service.send_command(drone_id, body.command, body.altitude_m)
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "accepted", "command": body.command.value}


@router.get("/{drone_id}/telemetry/latest", response_model=TelemetryResponse | None)
async def latest_telemetry(
    drone_id: UUID,
    _: Annotated[AuthPrincipal, Depends(require_auth)],
    service: Annotated[FleetService, Depends(get_fleet_service)],
) -> TelemetryResponse | None:
    try:
        sample = await service.latest_telemetry(drone_id)
    except DroneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if sample is None:
        return None
    return TelemetryResponse.model_validate(sample.model_dump())
