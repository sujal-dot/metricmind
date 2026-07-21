from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.models.schemas import ErrorResponse, HealthResponse, MetricsResponse, SalesListResponse
from app.services.database import get_db
from app.services.metrics_service import MetricsService
from app.services.sales_service import SalesService

router = APIRouter()


@router.get("/", response_model=HealthResponse, tags=["health"])
async def root() -> HealthResponse:
    return HealthResponse(status="success", message="MetricMind Backend Running")


@router.get("/sales", response_model=SalesListResponse, tags=["sales"])
def list_sales(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SalesListResponse:
    service = SalesService(db)
    items, total = service.list_sales(limit=limit, offset=offset)
    return SalesListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/metrics", response_model=MetricsResponse, tags=["metrics"])
def get_metrics() -> MetricsResponse:
    service = MetricsService()
    data = service.get_metrics()
    return MetricsResponse(**data)
