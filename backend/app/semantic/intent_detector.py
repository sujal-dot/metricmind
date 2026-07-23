"""Detect structured analytics intent from natural language questions."""
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("metricmind.semantic.intent")


class UserIntent(BaseModel):
    """Logical analytics intent, independent from Cube member names."""

    metrics: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    time_period: Optional[Dict[str, Any]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    ordering: Optional[Dict[str, str]] = None
    limit: Optional[int] = None
    granularity: Optional[str] = None
    comparison: Optional[str] = None


class IntentDetector:
    """Detect metrics, dimensions, periods, ranking, and granularity."""

    METRIC_PATTERNS: tuple[tuple[str, str], ...] = (
        ("average order value", "average_order_value"),
        ("aov", "average_order_value"),
        ("total customers", "customers"),
        ("number of customers", "customers"),
        ("total profit", "profit"),
        ("profit", "profit"),
        ("margin", "margin"),
        ("discount", "discount_amount"),
        ("total quantity", "quantity"),
        ("quantity", "quantity"),
        ("order count", "orders"),
        ("total orders", "orders"),
        ("orders", "orders"),
        ("revenue", "revenue"),
        ("sales", "revenue"),
    )

    DIMENSION_PATTERNS: tuple[tuple[str, str], ...] = (
        ("sub category", "sub_category"),
        ("subcategory", "sub_category"),
        ("category", "category"),
        ("region", "region"),
        ("state", "state"),
        ("country", "country"),
        ("customer", "customer"),
        ("customers", "customer"),
        ("product", "product"),
        ("products", "product"),
        ("segment", "segment"),
        ("employee", "employee"),
    )

    GRANULARITY_PATTERNS: tuple[tuple[str, str], ...] = (
        ("monthly", "month"),
        ("month", "month"),
        ("quarterly", "quarter"),
        ("quarter", "quarter"),
        ("weekly", "week"),
        ("week", "week"),
        ("daily", "day"),
        ("day", "day"),
        ("yearly", "year"),
        ("year", "year"),
    )

    def detect(self, question: str) -> UserIntent:
        question = question.strip()
        if not question:
            raise ValueError("Invalid user request: question cannot be empty")

        logger.info("Detecting semantic intent for question: %s", question)
        lowered = question.lower()
        intent = UserIntent()

        metric = self._detect_metric(lowered)
        intent.metrics = [metric]

        dimensions = self._detect_dimensions(lowered)
        if dimensions:
            intent.dimensions = dimensions

        intent.time_period = self._detect_time_period(lowered)
        intent.granularity = self._detect_granularity(lowered, dimensions)
        intent.ordering = self._detect_ordering(lowered, metric)
        intent.limit = self._detect_limit(lowered)
        intent.comparison = self._detect_comparison(lowered)

        if intent.comparison == "month_over_month" and intent.granularity is None:
            intent.granularity = "month"

        if not intent.dimensions and intent.granularity in {"month", "quarter", "week", "day", "year"}:
            intent.dimensions = [intent.granularity]

        logger.info("Detected semantic intent: %s", intent.model_dump())
        return intent

    def _detect_metric(self, question: str) -> str:
        for phrase, metric in self.METRIC_PATTERNS:
            if phrase in question:
                return metric
        return "revenue"

    def _detect_dimensions(self, question: str) -> List[str]:
        dimensions: List[str] = []
        for phrase, dimension in self.DIMENSION_PATTERNS:
            if phrase in question and dimension not in dimensions:
                dimensions.append(dimension)
        return dimensions

    def _detect_time_period(self, question: str) -> Optional[Dict[str, Any]]:
        time_period: Dict[str, Any] = {}
        year_match = re.search(r"\b(20\d{2})\b", question)
        if year_match:
            time_period["year"] = int(year_match.group(1))

        for phrase in (
            "this month",
            "last month",
            "this year",
            "last year",
            "this quarter",
            "last quarter",
            "today",
            "yesterday",
        ):
            if phrase in question:
                time_period["range"] = phrase
                break

        return time_period or None

    def _detect_granularity(self, question: str, dimensions: List[str]) -> Optional[str]:
        for phrase, granularity in self.GRANULARITY_PATTERNS:
            if phrase in question:
                return granularity
        if "trend" in question:
            return "month"
        if "compare" in question and "month" in question:
            return "month"
        if dimensions and dimensions[0] in {"month", "quarter", "week", "day", "year"}:
            return dimensions[0]
        return None

    def _detect_ordering(self, question: str, metric: str) -> Optional[Dict[str, str]]:
        if any(term in question for term in ("top", "highest", "largest", "best", "most")):
            return {"field": metric, "direction": "desc"}
        if any(term in question for term in ("bottom", "lowest", "smallest", "least")):
            return {"field": metric, "direction": "asc"}
        return None

    def _detect_limit(self, question: str) -> Optional[int]:
        explicit = re.search(r"\btop\s+(\d{1,3})\b", question)
        if explicit:
            return int(explicit.group(1))
        generic = re.search(r"\b(\d{1,3})\b", question)
        if generic and any(term in question for term in ("top", "bottom")):
            return int(generic.group(1))
        if "top" in question:
            return 10
        return None

    def _detect_comparison(self, question: str) -> Optional[str]:
        if "compare" in question and "this month" in question and "last month" in question:
            return "month_over_month"
        return None
