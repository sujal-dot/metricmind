import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api.semantic as semantic_api_module
from app.main import app
from app.auth.dependencies import get_current_user, require_csrf
from app.semantic.intent_detector import IntentDetector
from app.semantic.query_parser import QueryParser
from app.semantic.response_formatter import ResponseFormatter
from app.semantic.semantic_router import SemanticRouter

app.dependency_overrides[get_current_user] = lambda: {
    "id": 1,
    "email": "test@example.com",
    "role": "admin",
    "is_active": True,
}
app.dependency_overrides[require_csrf] = lambda: None

client = TestClient(app)


class FakeSemanticLLM:
    async def ainvoke(self, _messages):
        return AIMessage(content="Revenue increased steadily across the returned periods.")


class FakeCubeClient:
    def __init__(self):
        self.last_query = None

    async def load(self, query):
        self.last_query = query
        return {
            "data": [
                {"DimDate.month": "2025-01-01T00:00:00.000", "FactSales.revenue": "1000"},
                {"DimDate.month": "2025-02-01T00:00:00.000", "FactSales.revenue": "1200"},
            ]
        }


def test_intent_detection_for_monthly_revenue():
    detector = IntentDetector()
    intent = detector.detect("Show monthly revenue for 2025")
    assert intent.metrics == ["revenue"]
    assert intent.granularity == "month"
    assert intent.time_period == {"year": 2025}


def test_intent_detection_for_top_customers():
    detector = IntentDetector()
    intent = detector.detect("Top 10 customers by revenue")
    assert intent.metrics == ["revenue"]
    assert intent.dimensions == ["customer"]
    assert intent.limit == 10
    assert intent.ordering == {"field": "revenue", "direction": "desc"}


def test_query_parser_routes_to_cube_members():
    detector = IntentDetector()
    parser = QueryParser()
    intent = detector.detect("Show monthly revenue for 2025")
    query = parser.parse(intent)
    assert query["measures"] == ["FactSales.revenue"]
    assert query["timeDimensions"][0]["dimension"] == "DimDate.fullDate"
    assert query["timeDimensions"][0]["granularity"] == "month"
    assert query["timeDimensions"][0]["dateRange"] == ["2025-01-01", "2025-12-31"]
    assert "sql" not in str(query).lower()


def test_response_formatter_handles_empty_results():
    formatter = ResponseFormatter()
    formatted = formatter.format({"data": []})
    assert formatted.has_data is False
    assert formatted.row_count == 0
    assert "no rows" in formatted.summary.lower()


def test_semantic_router_uses_cube_and_generates_explanation():
    cube_client = FakeCubeClient()
    router = SemanticRouter(llm_provider="groq", llm=FakeSemanticLLM(), cube_client=cube_client)
    response = asyncio.run(router.process("Show monthly revenue for 2025"))
    assert response["provider"] == "groq"
    assert response["intent"]["metrics"] == ["revenue"]
    assert response["cube_response"]["data"]
    assert "sql" not in response["explanation"].lower()
    assert cube_client.last_query["measures"] == ["FactSales.revenue"]


def test_semantic_search_endpoint_returns_expected_json(monkeypatch):
    async def fake_process(question: str):
        return {
            "question": question,
            "intent": {
                "metrics": ["revenue"],
                "dimensions": ["month"],
                "time_period": {"year": 2025},
                "filters": {},
                "ordering": None,
                "limit": None,
                "granularity": "month",
                "comparison": None,
            },
            "cube_response": {"data": [{"FactSales.revenue": "1000"}]},
            "explanation": "Revenue increased steadily throughout 2025.",
            "provider": "groq",
        }

    monkeypatch.setattr(semantic_api_module, "SemanticRouter", lambda: SimpleNamespace(process=fake_process))
    response = client.post("/semantic-search", json={"question": "Show monthly revenue for 2025"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "groq"
    assert payload["intent"]["metrics"] == ["revenue"]
    assert "cube_response" in payload
    assert "explanation" in payload


def test_semantic_search_endpoint_handles_invalid_request(monkeypatch):
    async def fake_process(_question: str):
        raise ValueError("Invalid user request: question cannot be empty")

    monkeypatch.setattr(semantic_api_module, "SemanticRouter", lambda: SimpleNamespace(process=fake_process))
    response = client.post("/semantic-search", json={"question": ""})
    assert response.status_code == 400
    assert "Invalid user request" in response.json()["detail"]
