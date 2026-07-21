from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.services.database import get_engine


class MetricsService:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def get_metrics(self) -> dict:
        with self.engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT
                        COALESCE(SUM(sales_amount), 0) AS total_revenue,
                        COALESCE(SUM(profit_amount), 0) AS total_profit,
                        COALESCE(SUM(profit_amount), 0) / NULLIF(COALESCE(SUM(sales_amount), 0), 0) AS profit_margin,
                        COUNT(*) AS total_orders,
                        COUNT(DISTINCT customer_key) AS total_customers,
                        COALESCE(SUM(sales_amount), 0) / NULLIF(COUNT(*), 0) AS average_order_value
                    FROM fact_sales
                    """
                )
            ).one()

        return {
            "total_revenue": float(result[0] or 0),
            "total_profit": float(result[1] or 0),
            "profit_margin": float(result[2] or 0),
            "total_orders": int(result[3] or 0),
            "total_customers": int(result[4] or 0),
            "average_order_value": float(result[5] or 0),
        }
