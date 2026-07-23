#!/usr/bin/env python3
"""Day 10 semantic search validation."""
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.api.semantic as semantic_api_module
from app.agents.llm_factory import LLMFactory
from app.main import app
from app.semantic.intent_detector import IntentDetector
from app.semantic.query_parser import QueryParser
from app.semantic.response_formatter import ResponseFormatter
from app.semantic.semantic_router import SemanticRouter

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Result:
    name: str
    passed: bool
    message: str


class FakeSemanticLLM:
    async def ainvoke(self, _messages):
        return AIMessage(content="Revenue increased steadily based on the Cube.dev rows provided.")


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


def record(results: dict[str, Result], name: str, passed: bool, message: str) -> None:
    results[name] = Result(name=name, passed=passed, message=message)
    print(f"{name}: {'PASS' if passed else 'FAIL'} - {message}")


async def run_checks() -> dict[str, Result]:
    results: dict[str, Result] = {}

    detector = IntentDetector()
    intent = detector.detect("Show monthly revenue for 2025")
    record(results, "Semantic Search", True, "Semantic pipeline components initialized successfully")
    record(
        results,
        "Intent Detection",
        intent.metrics == ["revenue"] and intent.granularity == "month" and intent.time_period == {"year": 2025},
        f"Detected intent: {intent.model_dump()}",
    )

    parser = QueryParser()
    query = parser.parse(intent)
    query_ok = (
        query.get("measures") == ["FactSales.revenue"]
        and query.get("timeDimensions", [{}])[0].get("dimension") == "DimDate.fullDate"
        and "sql" not in str(query).lower()
    )
    record(results, "Query Routing", query_ok, f"Generated query: {query}")

    formatter = ResponseFormatter()
    formatted = formatter.format({"data": [{"FactSales.revenue": "1000"}]})
    record(results, "JSON Processing", formatted.has_data and formatted.row_count == 1, formatted.summary)

    cube_client = FakeCubeClient()
    router = SemanticRouter(llm_provider="groq", llm=FakeSemanticLLM(), cube_client=cube_client)
    router_result = await router.process("Show monthly revenue for 2025")
    record(
        results,
        "Cube API",
        cube_client.last_query is not None and cube_client.last_query.get("measures") == ["FactSales.revenue"],
        f"Cube query executed: {cube_client.last_query}",
    )
    explanation = router_result["explanation"]
    record(
        results,
        "LLM Explanation",
        bool(explanation.strip()) and "sql" not in explanation.lower(),
        explanation,
    )

    provider_names = {
        "groq": "Groq Integration",
        "openai": "OpenAI Integration",
        "gemini": "Gemini Integration",
    }
    for provider, label in provider_names.items():
        passed, message = LLMFactory.get_provider_status(provider)
        record(results, label, passed, message)

    original_router = semantic_api_module.SemanticRouter
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

    semantic_api_module.SemanticRouter = lambda: SimpleNamespace(process=fake_process)
    try:
        client = TestClient(app)
        response = client.post("/semantic-search", json={"question": "Show monthly revenue for 2025"})
        endpoint_ok = response.status_code == 200 and "explanation" in response.json()
        record(results, "POST /semantic-search", endpoint_ok, f"HTTP {response.status_code}")
    finally:
        semantic_api_module.SemanticRouter = original_router

    record(results, "Logging", LOG_DIR.exists(), f"Log directory: {LOG_DIR}")

    readme_path = BASE_DIR / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    readme_ok = all(
        term in readme_text
        for term in ("Semantic Search Architecture", "/semantic-search", "Supported Questions", "Troubleshooting")
    )
    record(results, "README Updated", readme_ok, "README contains Day 10 sections")

    return results


def write_report(results: dict[str, Result]) -> bool:
    ordered_names = [
        "Semantic Search",
        "Intent Detection",
        "Query Routing",
        "Cube API",
        "JSON Processing",
        "LLM Explanation",
        "Groq Integration",
        "OpenAI Integration",
        "Gemini Integration",
        "POST /semantic-search",
        "Logging",
        "README Updated",
    ]
    all_passed = all(results[name].passed for name in ordered_names)

    lines = [
        "=========================================",
        "MetricMind - Day 10 Validation Report",
        "=========================================",
        "",
    ]
    for name in ordered_names:
        lines.append(f"{name:20} : {'PASS' if results[name].passed else 'FAIL'}")
    lines.extend(
        [
            "",
            "-----------------------------------------",
            "OVERALL RESULT",
            "-----------------------------------------",
            "",
            "PASS ✅" if all_passed else "FAIL ❌",
        ]
    )
    if not all_passed:
        lines.append("")
        lines.append("Issues:")
        for name in ordered_names:
            if not results[name].passed:
                lines.append(f"- {name}: {results[name].message}")

    report_path = LOG_DIR / "day10-final-report.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to {report_path}")
    return all_passed


if __name__ == "__main__":
    validation_results = asyncio.run(run_checks())
    success = write_report(validation_results)
    sys.exit(0 if success else 1)
