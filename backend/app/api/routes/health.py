from fastapi import APIRouter, Request

from app.api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings = request.app.state.container.settings
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        env=settings.app_env,
        simulation=settings.is_simulation,
    )
