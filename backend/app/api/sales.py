from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.schemas import SalesListResponse
from app.services.database import get_db
from app.services.sales_service import SalesService

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=SalesListResponse)
def list_sales(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SalesListResponse:
    service = SalesService(db)
    items, total = service.list_sales(limit=limit, offset=offset)
    return SalesListResponse(items=items, total=total, limit=limit, offset=offset)
