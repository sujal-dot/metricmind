from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.models.schemas import MetricsBase, MetricsResponse
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=MetricsResponse)
async def get_metrics(
    _: dict = Depends(get_current_user),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    region: str | None = Query(default=None),
    category: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    ship_mode: str | None = Query(default=None),
) -> MetricsResponse:
    service = MetricsService()
    data = await service.get_metrics(
        date_from=date_from,
        date_to=date_to,
        region=region,
        category=category,
        segment=segment,
        ship_mode=ship_mode,
    )

    prior_raw = data.pop("_prior", None)
    deltas_raw = data.pop("_deltas_pct", None)

    prior_metrics = MetricsBase(**prior_raw) if prior_raw else None

    period_change_pct: dict[str, Any] = {}
    if deltas_raw:
        for k, v in deltas_raw.items():
            if v is None or (isinstance(v, float) and v != v) or isinstance(v, float) and (v == float("inf") or v == float("-inf")):
                period_change_pct[k] = None
            else:
                period_change_pct[k] = round(float(v), 2)

    return MetricsResponse(
        **data,
        prior_metrics=prior_metrics,
        period_change_pct=period_change_pct,
    )
