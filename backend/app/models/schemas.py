from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "success"})
    message: str = Field(..., json_schema_extra={"example": "MetricMind Backend Running"})


class SalesItem(BaseModel):
    order_id: str
    sales: float
    quantity: int
    profit: float
    discount: float


class SalesListResponse(BaseModel):
    items: List[SalesItem]
    total: int
    limit: int
    offset: int


class MetricsResponse(BaseModel):
    total_revenue: float
    total_profit: float
    profit_margin: float
    total_orders: int
    total_customers: int
    average_order_value: float


class ErrorResponse(BaseModel):
    detail: str


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
