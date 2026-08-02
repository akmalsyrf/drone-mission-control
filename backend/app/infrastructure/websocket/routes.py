from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/telemetry")
async def telemetry_ws(
    websocket: WebSocket,
    drone_id: str | None = Query(default=None),
) -> None:
    await websocket.accept()
    hub = websocket.app.state.container.telemetry_hub

    target: UUID | None
    if drone_id is None or drone_id in {"*", "all"}:
        target = None
    else:
        try:
            target = UUID(drone_id)
        except ValueError:
            await websocket.close(code=1008, reason="Invalid drone_id")
            return

    logger.info("ws_client_connected", drone_id=drone_id or "*")
    try:
        async for sample in hub.subscribe(target):
            await websocket.send_text(sample.model_dump_json())
    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", drone_id=drone_id or "*")
    except Exception:
        logger.exception("ws_error")
        await websocket.close(code=1011)
