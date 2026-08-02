"""Convert logical user intent into valid Cube.dev API queries."""
import logging
from datetime import date, timedelta
from typing import Any, Dict, List

from app.semantic.intent_detector import UserIntent

logger = logging.getLogger("metricmind.semantic.parser")


class QueryParser:
    """Translate semantic intent to Cube member names and query structure."""

    METRIC_TO_MEMBER = {
        "revenue": "FactSales.revenue",
        "profit": "FactSales.profit",
        "orders": "FactSales.totalOrders",
        "quantity": "FactSales.totalQuantity",
        "customers": "FactSales.totalCustomers",
        "average_order_value": "FactSales.averageOrderValue",
        "discount_amount": "FactSales.discountAmount",
        "margin": "FactSales.margin",
    }

    DIMENSION_TO_MEMBER = {
        "region": "DimRegion.region",
        "state": "DimRegion.state",
        "country": "DimRegion.country",
        "customer": "DimCustomer.customerName",
        "segment": "DimCustomer.segment",
        "product": "DimProduct.productName",
        "category": "DimProduct.category",
        "sub_category": "DimProduct.subCategory",
        "employee": "DimEmployee.employeeName",
    }

    TIME_DIMENSION = "DimDate.fullDate"

    def parse(self, intent: UserIntent) -> Dict[str, Any]:
        logger.info("Parsing semantic intent into Cube query: %s", intent.model_dump())

        measures = [self._metric_member(metric) for metric in intent.metrics]
        dimensions = self._dimension_members(intent.dimensions, intent=intent)
        cube_query: Dict[str, Any] = {"measures": measures}
        if dimensions:
            cube_query["dimensions"] = dimensions

        time_dimension = self._build_time_dimension(intent)
        if time_dimension:
            cube_query["timeDimensions"] = [time_dimension]

        if intent.ordering:
            order_field = self._order_field(intent, measures, dimensions)
            cube_query["order"] = {order_field: intent.ordering["direction"]}

        if intent.limit:
            cube_query["limit"] = intent.limit

        logger.info("Generated Cube query: %s", cube_query)
        return cube_query

    def _metric_member(self, metric: str) -> str:
        return self.METRIC_TO_MEMBER.get(metric, "FactSales.revenue")

    def _dimension_members(self, dimensions: List[str], intent: UserIntent | None = None) -> List[str]:
        members: List[str] = []
        is_customer_count = intent and "customers" in intent.metrics and not intent.limit
        for dimension in dimensions:
            if is_customer_count and dimension == "customer":
                continue
            member = self.DIMENSION_TO_MEMBER.get(dimension)
            if member and member not in members:
                members.append(member)
        return members

    def _order_field(self, intent: UserIntent, measures: List[str], dimensions: List[str]) -> str:
        if dimensions and intent.limit:
            return measures[0]
        return measures[0]

    def _build_time_dimension(self, intent: UserIntent) -> Dict[str, Any] | None:
        if intent.comparison == "month_over_month":
            start, end = self._current_and_previous_month_range()
            return {
                "dimension": self.TIME_DIMENSION,
                "dateRange": [start, end],
                "granularity": "month",
            }

        if not intent.time_period and not intent.granularity:
            return None

        time_dimension: Dict[str, Any] = {"dimension": self.TIME_DIMENSION}
        if intent.time_period:
            if "range" in intent.time_period:
                time_dimension["dateRange"] = intent.time_period["range"]
            elif "year" in intent.time_period:
                year = intent.time_period["year"]
                time_dimension["dateRange"] = [f"{year}-01-01", f"{year}-12-31"]

        if intent.granularity in {"day", "week", "month", "quarter", "year"}:
            time_dimension["granularity"] = intent.granularity

        return time_dimension

    @staticmethod
    def _current_and_previous_month_range() -> tuple[str, str]:
        today = date.today()
        first_this_month = today.replace(day=1)
        last_previous_month = first_this_month - timedelta(days=1)
        first_previous_month = last_previous_month.replace(day=1)
        next_month_anchor = (first_this_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        last_this_month = next_month_anchor - timedelta(days=1)
        return first_previous_month.isoformat(), last_this_month.isoformat()
