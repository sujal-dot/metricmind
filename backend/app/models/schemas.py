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


class MetricsBase(BaseModel):
    total_revenue: float
    total_profit: float
    profit_margin: float
    total_orders: int
    total_customers: int
    average_order_value: float


class MetricsResponse(MetricsBase):
    prior_metrics: Optional[MetricsBase] = None
    period_change_pct: Dict[str, Optional[float]] = Field(default_factory=dict)


class MonthlyAnalyticsPoint(BaseModel):
    label: str
    revenue: float
    profit: float
    orders: int


class AnalyticsDataPoint(BaseModel):
    name: str
    value: float


class AnalyticsChartsResponse(BaseModel):
    monthly: List[MonthlyAnalyticsPoint]
    by_category: List[AnalyticsDataPoint]
    by_region: List[AnalyticsDataPoint]
    top_products: List[AnalyticsDataPoint]
    top_customers: List[AnalyticsDataPoint]


class ErrorResponse(BaseModel):
    detail: str


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int


class BIQuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=0,
        max_length=4000,
        json_schema_extra={"example": "What was the total revenue last month?"},
    )


class BIAnswerResponse(BaseModel):
    question: str
    answer: str
    source: str
    provider: str
    cube_trace: Optional[Dict[str, Any]] = Field(
        None,
        description="Transparency payload rendered by the frontend View API button.",
    )
    cube_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Cube.dev JSON response rendered by the frontend View JSON button.",
    )


class SemanticSearchRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=0,
        max_length=4000,
        json_schema_extra={"example": "Show monthly revenue for 2025"},
    )


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
    cube_trace: Optional[Dict[str, Any]] = Field(
        None,
        description="Transparency payload rendered by the frontend View API button.",
    )
    cube_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Cube.dev JSON response rendered by the frontend View JSON button.",
    )


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
        min_length=1,
        max_length=4000,
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
    cube_trace: Optional[Dict[str, Any]] = Field(
        None,
        description="Transparency payload rendered by the frontend View API button.",
    )
    cube_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Cube.dev JSON response rendered by the frontend View JSON button.",
    )


# ---------------------------------------------------------------------------
# Governance / Transparency (Day 16)
# ---------------------------------------------------------------------------
class GovernanceValidationRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        json_schema_extra={"example": "SELECT * FROM Orders"},
    )
    route: Optional[str] = Field(
        None,
        max_length=255,
        json_schema_extra={"example": "/ask"},
        description="Optional endpoint the question is targeted at, for logging.",
    )


class SecurityDecisionSchema(BaseModel):
    allowed: bool
    block_reason: Optional[str] = None
    block_code: Optional[str] = None
    suggested_filters: List[str] = Field(default_factory=list)
    has_sql_injection: bool = False
    has_sql_request: bool = False
    is_expensive: bool = False
    matched_reasons: List[str] = Field(default_factory=list)


class GovernanceValidationResponse(BaseModel):
    question: str
    decision: SecurityDecisionSchema
    cube_trace: Optional[Dict[str, Any]] = None
    cube_json: Optional[Dict[str, Any]] = None


class CubeTraceSchema(BaseModel):
    """Schema the frontend reads for the View API / View JSON buttons.

    All fields are redacted by the backend — no tokens or secrets leak here.
    """

    endpoint: str = Field(..., json_schema_extra={"example": "/cubejs-api/v1/load"})
    method: str = Field(..., json_schema_extra={"example": "POST"})
    request_payload: Dict[str, Any] = Field(default_factory=dict)
    query_parameters: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(..., json_schema_extra={"example": 245.18})
    response_status: int = Field(..., json_schema_extra={"example": 200})
    response_size_bytes: int = Field(..., json_schema_extra={"example": 3892})
