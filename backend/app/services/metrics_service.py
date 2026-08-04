import logging
from datetime import date, timedelta

from app.agents.cube_client import CubeClient

logger = logging.getLogger("metricmind.services.metrics_service")

_cube_client: CubeClient | None = None


def _get_cube_client() -> CubeClient:
    global _cube_client
    if _cube_client is None:
        _cube_client = CubeClient()
    return _cube_client


class MetricsService:
    def __init__(self, cube_client: CubeClient | None = None):
        self.client = cube_client or _get_cube_client()

    async def get_metrics(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        region: str | None = None,
        category: str | None = None,
        segment: str | None = None,
        ship_mode: str | None = None,
    ) -> dict:
        measures = [
            "FactSales.revenue",
            "FactSales.profit",
            "FactSales.totalOrders",
            "FactSales.totalCustomers",
            "FactSales.averageOrderValue",
            "FactSales.margin",
        ]

        filters = self._build_filters(region=region, category=category, segment=segment, ship_mode=ship_mode)
        time_dimensions = self._build_time_dimensions(date_from=date_from, date_to=date_to)

        query = {
            "measures": measures,
            "filters": filters,
            "timeDimensions": time_dimensions,
        }

        try:
            result = await self.client.load(query)
            current_row = (result.get("data") or [{}])[0]
        except Exception as exc:
            logger.exception("Cube.dev call failed for current metrics: %s", exc)
            current_row = {}

        current = self._extract_metrics(current_row)

        prior_filters = list(filters)
        prior_time_dimensions = self._build_prior_time_dimensions(date_from, date_to)

        prior_query = {
            "measures": measures,
            "filters": prior_filters,
            "timeDimensions": prior_time_dimensions,
        }

        try:
            prior_result = await self.client.load(prior_query)
            prior_row = (prior_result.get("data") or [{}])[0]
        except Exception as exc:
            logger.exception("Cube.dev call failed for prior metrics: %s", exc)
            prior_row = {}

        prior = self._extract_metrics(prior_row)

        deltas_pct = self._calculate_deltas_pct(current, prior)

        current["_prior"] = prior
        current["_deltas_pct"] = deltas_pct

        return current

    @staticmethod
    def _build_filters(
        region: str | None,
        category: str | None,
        segment: str | None = None,
        ship_mode: str | None = None,
    ) -> list[dict]:
        filters = []
        if region:
            filters.append({
                "member": "DimRegion.region",
                "operator": "equals",
                "values": [region],
            })
        if category:
            filters.append({
                "member": "DimProduct.category",
                "operator": "equals",
                "values": [category],
            })
        if segment:
            filters.append({
                "member": "DimCustomer.segment",
                "operator": "equals",
                "values": [segment],
            })
        if ship_mode:
            filters.append({
                "member": "FactSales.shipMode",
                "operator": "equals",
                "values": [ship_mode],
            })
        return filters

    @staticmethod
    def _build_time_dimensions(date_from: date | None, date_to: date | None) -> list[dict]:
        if not date_from and not date_to:
            return []

        date_range: list[str] = []
        if date_from:
            date_range.append(date_from.isoformat())
        else:
            date_range.append("1970-01-01")
        if date_to:
            date_range.append(date_to.isoformat())
        else:
            date_range.append("2999-12-31")

        return [{
            "dimension": "DimDate.fullDate",
            "dateRange": date_range,
        }]

    @staticmethod
    def _build_prior_time_dimensions(date_from: date | None, date_to: date | None) -> list[dict]:
        if not date_from or not date_to:
            return []

        duration = date_to - date_from
        days = duration.days + 1

        prior_date_to = date_from - timedelta(days=1)
        prior_date_from = prior_date_to - timedelta(days=days - 1)

        return [{
            "dimension": "DimDate.fullDate",
            "dateRange": [prior_date_from.isoformat(), prior_date_to.isoformat()],
        }]

    @staticmethod
    def _extract_metrics(row: dict) -> dict:
        revenue = float(row.get("FactSales.revenue") or 0)
        profit = float(row.get("FactSales.profit") or 0)
        orders = int(row.get("FactSales.totalOrders") or 0)
        customers = int(row.get("FactSales.totalCustomers") or 0)
        aov_cube = float(row.get("FactSales.averageOrderValue") or 0)
        margin_cube = float(row.get("FactSales.margin") or 0)

        if aov_cube == 0 and orders > 0:
            aov = revenue / orders if orders > 0 else 0.0
        else:
            aov = aov_cube

        if margin_cube > 0:
            profit_margin = margin_cube * 100
        else:
            profit_margin = (profit / revenue * 100) if revenue != 0 else 0.0

        return {
            "total_revenue": revenue,
            "total_profit": profit,
            "profit_margin": profit_margin,
            "total_orders": orders,
            "total_customers": customers,
            "average_order_value": aov,
        }

    @staticmethod
    def _calculate_deltas_pct(current: dict, prior: dict) -> dict:
        deltas = {}
        for key in ["total_revenue", "total_profit", "profit_margin", "total_orders", "total_customers", "average_order_value"]:
            cur = current.get(key, 0)
            prv = prior.get(key, 0)
            if prv == 0:
                deltas[key] = None if cur == 0 else float("inf") if cur > 0 else float("-inf")
            else:
                deltas[key] = ((cur - prv) / abs(prv)) * 100
        return deltas
