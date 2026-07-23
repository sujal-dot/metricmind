from typing import Generic, List, TypeVar, Any, Dict, Optional

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


class BIQuestionRequest(BaseModel):
    question: str = Field(..., json_schema_extra={"example": "What was the total revenue last month?"})


class BIAnswerResponse(BaseModel):
    question: str
    answer: str
    source: str
    provider: str


class SemanticSearchRequest(BaseModel):
    question: str = Field(..., json_schema_extra={"example": "Show monthly revenue for 2025"})


class SemanticSearchIntent(BaseModel):
    metrics: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    time_period: Optional[Dict[str, Any]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    ordering: Optional[Dict[str, str]] = None
    limit: Optional[int] = None
    granularity: Optional[str] = None
    comparison: Optional[str] = None


class SemanticSearchResponse(BaseModel):
    question: str
    intent: SemanticSearchIntent
    cube_response: Dict[str, Any]
    explanation: str
    provider: str
