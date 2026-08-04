from datetime import date

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.models.schemas import AnalyticsChartsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/charts", response_model=AnalyticsChartsResponse)
async def get_analytics_charts(
    _: dict = Depends(get_current_user),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    category: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    ship_mode: str | None = Query(default=None),
) -> AnalyticsChartsResponse:
    service = AnalyticsService()
    data = await service.get_charts(
        date_from=date_from,
        date_to=date_to,
        region=region,
        category=category,
        segment=segment,
        ship_mode=ship_mode,
    )
    return AnalyticsChartsResponse(**data)
