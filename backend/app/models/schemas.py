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


class ExplainSummary(BaseModel):
    region: str = Field(..., json_schema_extra={"example": "Europe"})
    period: Optional[str] = Field(None, json_schema_extra={"example": "last month"})
    revenue: float = Field(..., json_schema_extra={"example": 1420000})
    cost: float = Field(..., json_schema_extra={"example": 1180000})
    shipping_cost: float = Field(..., json_schema_extra={"example": 165000})
    discount_amount: float = Field(..., json_schema_extra={"example": 78000})
    profit: float = Field(..., json_schema_extra={"example": 240000})
    margin: float = Field(..., json_schema_extra={"example": 16.9})
    orders: int = Field(..., json_schema_extra={"example": 2840})
    customers: int = Field(..., json_schema_extra={"example": 612})
    aov: float = Field(..., json_schema_extra={"example": 500})
    primary_metric: str = Field(..., json_schema_extra={"example": "margin"})
    direction_hint: str = Field(..., json_schema_extra={"example": "down"})
    period_deltas_pct: Dict[str, Any] = Field(default_factory=dict)
    period_deltas_abs: Dict[str, Any] = Field(default_factory=dict)


class ExplainRequest(BaseModel):
    question: str = Field(
        ...,
        json_schema_extra={"example": "Why did European margin decrease?"},
    )


class ExplainResponse(BaseModel):
    question: str
    summary: ExplainSummary
    possible_reasons: List[str] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [
                "Shipping costs increased by 14%, compressing gross margin.",
                "Discounts were higher than the prior period, reducing per-order profitability.",
                "Product / COGS costs rose by 8%, outpacing revenue growth.",
            ]
        },
    )
    confidence: int = Field(..., json_schema_extra={"example": 92})
    confidence_breakdown: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [
                "Review shipping partners and negotiate rates.",
                "Reduce excessive discounts.",
                "Optimize high-cost product pricing.",
            ]
        },
    )
    provider: str = Field(..., json_schema_extra={"example": "Groq"})
    data_source: str = Field("demo", json_schema_extra={"example": "cube_api"})
    narrative: Optional[str] = Field(None, json_schema_extra={"example": "Optional LLM synthesis text"})

