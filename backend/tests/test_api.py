import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.main as main_module
import app.services.sales_service as sales_service_module
import app.services.metrics_service as metrics_service_module
from app.main import app
from app.auth.dependencies import get_current_user, require_csrf
from app.agents.bi_agent import BIAgent
from app.agents.llm_factory import LLMFactory
from app.agents.prompts import BI_ANALYST_SYSTEM_PROMPT

app.dependency_overrides[get_current_user] = lambda: {
    "id": 1,
    "email": "test@example.com",
    "role": "admin",
    "is_active": True,
}
app.dependency_overrides[require_csrf] = lambda: None

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["message"] == "MetricMind Backend Running"


def test_sales_endpoint():
    original_service = sales_service_module.SalesService

    class FakeSalesService:
        def __init__(self, _db):
            pass

        def list_sales(self, limit: int = 100, offset: int = 0):
            return (
                [
                    {
                        "order_id": "CA-2014-100006",
                        "sales": 120.5,
                        "quantity": 2,
                        "profit": 20.1,
                        "discount": 0.0,
                    }
                ],
                1,
            )

    sales_service_module.SalesService = FakeSalesService
    try:
        response = client.get("/api/v1/sales", params={"limit": 5, "offset": 0})
    finally:
        sales_service_module.SalesService = original_service

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
    original_service = metrics_service_module.MetricsService

    class FakeMetricsService:
        async def get_metrics(self, **kwargs):
            return {
                "total_revenue": 1000.0,
                "total_profit": 120.0,
                "profit_margin": 0.12,
                "total_orders": 20,
                "total_customers": 10,
                "average_order_value": 50.0,
            }

    metrics_service_module.MetricsService = FakeMetricsService
    try:
        response = client.get("/api/v1/metrics")
    finally:
        metrics_service_module.MetricsService = original_service

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


def test_system_prompt_forbids_sql_and_requires_cube():
    assert "NEVER generate SQL" in BI_ANALYST_SYSTEM_PROMPT
    assert "NEVER access PostgreSQL directly" in BI_ANALYST_SYSTEM_PROMPT
    assert "Cube.dev" in BI_ANALYST_SYSTEM_PROMPT


def test_llm_factory_rejects_unsupported_provider():
    try:
        LLMFactory.create_llm(provider="invalid")  # type: ignore[arg-type]
    except ValueError as exc:
        assert "Unsupported LLM provider" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported provider")


class FakeToolAwareLLM:
    def bind_tools(self, _tools):
        return self

    async def ainvoke(self, messages):
        if any(getattr(message, "tool_call_id", None) for message in messages):
            return AIMessage(content="Revenue last month was 125000. This came from Cube API analytics.")
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "cube_query",
                    "args": {
                        "query": {
                            "measures": ["FactSales.revenue"],
                            "timeDimensions": [
                                {"dimension": "DimDate.fullDate", "dateRange": "last month"}
                            ],
                        }
                    },
                    "id": "tool_call_1",
                    "type": "tool_call",
                }
            ],
        )


class FakeCubeTool:
    name = "cube_query"

    async def ainvoke(self, args):
        assert args["query"]["measures"] == ["FactSales.revenue"]
        return '{"data":[{"FactSales.revenue":"125000"}]}'


def test_bi_agent_uses_cube_tool_flow():
    import asyncio

    agent = BIAgent(llm_provider="groq", llm=FakeToolAwareLLM(), tools=[FakeCubeTool()])
    response = asyncio.run(agent.ask("What was the total revenue last month?"))
    assert response["source"] == "Cube API"
    assert response["provider"] == "groq"
    assert "125000" in response["answer"]
    assert "SQL" not in response["answer"].upper()


def test_ask_endpoint_returns_expected_json(monkeypatch):
    async def fake_ask(question: str):
        return {
            "question": question,
            "answer": "Revenue last month was 125000.",
            "source": "Cube API",
            "provider": "groq",
        }

    monkeypatch.setattr(main_module, "BIAgent", lambda: SimpleNamespace(ask=fake_ask))
    response = client.post("/ask", json={"question": "What was the total revenue last month?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "What was the total revenue last month?"
    assert payload["answer"] == "Revenue last month was 125000."
    assert payload["source"] == "Cube API"
    assert payload["provider"] == "groq"
    assert "cube_trace" in payload
    assert "cube_json" in payload


def test_ask_endpoint_handles_invalid_request(monkeypatch):
    async def fake_ask(question: str):
        raise ValueError("Invalid user request: question cannot be empty")

    monkeypatch.setattr(main_module, "BIAgent", lambda: SimpleNamespace(ask=fake_ask))
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 400
    assert "Invalid user request" in response.json()["detail"]
