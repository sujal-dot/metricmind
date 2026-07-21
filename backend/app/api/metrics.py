from fastapi import APIRouter

from app.models.schemas import MetricsResponse
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    service = MetricsService()
    data = service.get_metrics()
    return MetricsResponse(**data)
