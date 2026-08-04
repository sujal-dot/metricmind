import asyncio
import logging
from datetime import date, datetime

from app.agents.cube_client import CubeClient

logger = logging.getLogger("metricmind.services.analytics_service")

_cube_client: CubeClient | None = None


def _get_cube_client() -> CubeClient:
    global _cube_client
    if _cube_client is None:
        _cube_client = CubeClient()
    return _cube_client


class AnalyticsService:
    def __init__(self, cube_client: CubeClient | None = None):
        self.client = cube_client or _get_cube_client()

    async def get_charts(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        region: str | None = None,
        category: str | None = None,
        segment: str | None = None,
        ship_mode: str | None = None,
    ) -> dict:
        filters = self._build_filters(region=region, category=category, segment=segment, ship_mode=ship_mode)
        time_dimensions = self._build_time_dimensions(date_from=date_from, date_to=date_to)

        monthly_query = {
            "measures": ["FactSales.revenue", "FactSales.profit", "FactSales.totalOrders"],
            "timeDimensions": [
                {
                    "dimension": "DimDate.fullDate",
                    "granularity": "month",
                    **({"dateRange": time_dimensions[0]["dateRange"]} if time_dimensions else {}),
                }
            ],
            "filters": filters,
            "order": {"DimDate.fullDate": "asc"},
        }

        by_category_query = {
            "measures": ["FactSales.revenue"],
            "dimensions": ["DimProduct.category"],
            "timeDimensions": time_dimensions,
            "filters": filters,
            "order": {"FactSales.revenue": "desc"},
            "limit": 20,
        }

        by_region_query = {
            "measures": ["FactSales.revenue"],
            "dimensions": ["DimRegion.region"],
            "timeDimensions": time_dimensions,
            "filters": filters,
            "order": {"FactSales.revenue": "desc"},
            "limit": 20,
        }

        top_products_query = {
            "measures": ["FactSales.revenue"],
            "dimensions": ["DimProduct.productName"],
            "timeDimensions": time_dimensions,
            "filters": filters,
            "order": {"FactSales.revenue": "desc"},
            "limit": 50,
        }

        top_customers_query = {
            "measures": ["FactSales.revenue"],
            "dimensions": ["DimCustomer.customerName"],
            "timeDimensions": time_dimensions,
            "filters": filters,
            "order": {"FactSales.revenue": "desc"},
            "limit": 50,
        }

        coros = [
            self._safe_load(monthly_query, "monthly"),
            self._safe_load(by_category_query, "by_category"),
            self._safe_load(by_region_query, "by_region"),
            self._safe_load(top_products_query, "top_products"),
            self._safe_load(top_customers_query, "top_customers"),
        ]

        monthly_raw, by_category_raw, by_region_raw, top_products_raw, top_customers_raw = await asyncio.gather(*coros)

        return {
            "monthly": self._shape_monthly(monthly_raw),
            "by_category": self._shape_data_points(by_category_raw, "DimProduct.category", "Unknown"),
            "by_region": self._shape_data_points(by_region_raw, "DimRegion.region", "Unknown"),
            "top_products": self._shape_data_points(top_products_raw, "DimProduct.productName", "Unknown Product"),
            "top_customers": self._shape_data_points(top_customers_raw, "DimCustomer.customerName", "Unknown Customer"),
        }

    async def _safe_load(self, query: dict, name: str) -> list[dict]:
        try:
            result = await self.client.load(query)
            data = result.get("data") or []
            logger.info("Cube.dev %s query returned %d rows", name, len(data))
            return data
        except Exception as exc:
            logger.exception("Cube.dev %s query failed: %s", name, exc)
            return []

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
    def _shape_monthly(rows: list[dict]) -> list[dict]:
        result = []
        for row in rows:
            time_val = row.get("DimDate.fullDate.month") or row.get("DimDate.fullDate")
            label = AnalyticsService._format_month_label(time_val)

            revenue = float(row.get("FactSales.revenue") or 0)
            profit = float(row.get("FactSales.profit") or 0)
            orders = int(row.get("FactSales.totalOrders") or 0)

            result.append({
                "label": label,
                "revenue": revenue,
                "profit": profit,
                "orders": orders,
            })
        return result

    @staticmethod
    def _format_month_label(value: str | None) -> str:
        if not value:
            return "Unknown"

        formats_to_try = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m",
        ]

        parsed = None
        for fmt in formats_to_try:
            try:
                parsed = datetime.strptime(value, fmt)
                break
            except (ValueError, TypeError):
                continue

        if parsed is None:
            return value[:7] if isinstance(value, str) else str(value)

        return parsed.strftime("%b %Y")

    @staticmethod
    def _shape_data_points(rows: list[dict], dim_key: str, default_name: str) -> list[dict]:
        result = []
        for row in rows:
            name = row.get(dim_key) or default_name
            value = float(row.get("FactSales.revenue") or 0)

            result.append({
                "name": str(name),
                "value": value,
            })
        return result
