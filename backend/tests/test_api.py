import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["message"] == "MetricMind Backend Running"


def test_sales_endpoint():
    response = client.get("/sales", params={"limit": 5, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert "total" in payload
    assert payload["limit"] == 5
    assert payload["offset"] == 0
    if payload["items"]:
        item = payload["items"][0]
        assert "order_id" in item
        assert "sales" in item
        assert "quantity" in item
        assert "profit" in item
        assert "discount" in item


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    payload = response.json()
    expected_fields = [
        "total_revenue",
        "total_profit",
        "profit_margin",
        "total_orders",
        "total_customers",
        "average_order_value",
    ]
    for field in expected_fields:
        assert field in payload
