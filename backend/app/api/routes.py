from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse, tags=["health"])
async def root() -> HealthResponse:
    return HealthResponse(status="success", message="MetricMind Backend Running")
