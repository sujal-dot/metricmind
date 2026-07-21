from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.schemas import SalesItem
from app.services.database import get_engine


class SalesService:
    def __init__(self, db: Session):
        self.db = db

    def list_sales(self, limit: int = 100, offset: int = 0) -> tuple[List[SalesItem], int]:
        engine = get_engine()
        with engine.connect() as connection:
            row_count = connection.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar_one()
            rows = connection.execute(
                text(
                    """
                    SELECT order_id, sales_amount AS sales, quantity, profit_amount AS profit, discount
                    FROM fact_sales
                    ORDER BY sales_key
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": limit, "offset": offset},
            ).fetchall()

        items = [
            SalesItem(
                order_id=row[0],
                sales=float(row[1] or 0),
                quantity=int(row[2] or 0),
                profit=float(row[3] or 0),
                discount=float(row[4] or 0),
            )
            for row in rows
        ]
        return items, int(row_count)
