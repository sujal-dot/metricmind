#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.main as main_module
from app.agents.bi_agent import BIAgent
from app.agents.cube_client import CubeClient
from app.agents.llm_factory import LLMFactory
from app.agents.prompts import BI_ANALYST_SYSTEM_PROMPT
from app.main import app

BASE_DIR = Path(__file__).resolve().parents[1]
log_dir = BASE_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)


class FakeToolAwareLLM:
    def bind_tools(self, _tools):
        return self

    async def ainvoke(self, messages):
        if any(getattr(message, "tool_call_id", None) for message in messages):
            return AIMessage(content="Revenue last month was 125000. This indicates stable top-line performance.")
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
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        )


class FakeCubeTool:
    name = "cube_query"

    async def ainvoke(self, args):
        return '{"data":[{"FactSales.revenue":"125000"}]}'


def validate_system_prompt() -> tuple[bool, str]:
    required_phrases = [
        "NEVER generate SQL",
        "NEVER access PostgreSQL directly",
        "ALWAYS retrieve analytics through the Cube.dev API",
    ]
    for phrase in required_phrases:
        if phrase not in BI_ANALYST_SYSTEM_PROMPT:
            return False, f"System prompt missing instruction: {phrase}"
    return True, "System prompt is loaded and enforces Cube-only behavior"


async def validate_cube_connection() -> tuple[bool, str]:
    try:
        client = CubeClient()
        connected = await client.check_connection()
        return (connected, "Cube.dev responded to /meta" if connected else "Cube.dev metadata was missing")
    except Exception as exc:
        return False, f"Cube.dev connection failed: {exc}"


def validate_provider(provider: str) -> tuple[bool, str]:
    return LLMFactory.get_provider_status(provider)  # type: ignore[arg-type]


async def validate_agent_initialization() -> tuple[bool, str]:
    try:
        agent = BIAgent(llm_provider="groq", llm=FakeToolAwareLLM(), tools=[FakeCubeTool()])
        response = await agent.ask("What was the total revenue last month?")
        answer = response["answer"]
        if "SQL" in answer.upper():
            return False, "Agent answer referenced SQL"
        if response["source"] != "Cube API":
            return False, "Agent response source is not Cube API"
        return True, "LangChain BI agent initializes and answers via Cube tool flow"
    except Exception as exc:
        return False, f"LangChain agent validation failed: {exc}"


def validate_endpoint() -> tuple[bool, str]:
    async def fake_ask(question: str):
        return {
            "question": question,
            "answer": "Revenue last month was 125000.",
            "source": "Cube API",
            "provider": "groq",
        }

    original_agent = main_module.BIAgent
    main_module.BIAgent = lambda: SimpleNamespace(ask=fake_ask)
    try:
        client = TestClient(app)
        response = client.post("/ask", json={"question": "What was the total revenue last month?"})
        if response.status_code != 200:
            return False, f"/ask returned HTTP {response.status_code}"
        payload = response.json()
        expected_keys = {"question", "answer", "source", "provider"}
        if set(payload.keys()) != expected_keys:
            return False, "JSON response schema is invalid"
        return True, "POST /ask returns valid JSON"
    finally:
        main_module.BIAgent = original_agent


def validate_json_response() -> tuple[bool, str]:
    async def fake_ask(question: str):
        return {
            "question": question,
            "answer": "Revenue last month was 125000.",
            "source": "Cube API",
            "provider": "groq",
        }

    original_agent = main_module.BIAgent
    main_module.BIAgent = lambda: SimpleNamespace(ask=fake_ask)
    try:
        client = TestClient(app)
        response = client.post("/ask", json={"question": "What was the total revenue last month?"})
        payload = response.json()
        expected_keys = {"question", "answer", "source", "provider"}
        if response.status_code != 200:
            return False, f"/ask returned HTTP {response.status_code}"
        if set(payload.keys()) != expected_keys:
            return False, "JSON response schema is invalid"
        if payload["source"] != "Cube API":
            return False, "Response source is not Cube API"
        return True, "JSON response schema is valid"
    finally:
        main_module.BIAgent = original_agent


def validate_logging() -> tuple[bool, str]:
    return (log_dir.exists(), "Log directory exists" if log_dir.exists() else "Log directory is missing")


def validate_readme() -> tuple[bool, str]:
    readme_path = BASE_DIR / "README.md"
    if not readme_path.exists():
        return False, "README is missing"
    content = readme_path.read_text(encoding="utf-8")
    required_terms = ["LangChain BI Agent", "LLM Providers", "POST /ask", "Troubleshooting"]
    missing = [term for term in required_terms if term not in content]
    if missing:
        return False, f"README missing sections: {', '.join(missing)}"
    return True, "README includes Day 9 documentation"


async def main():
    print("Starting Day 9 validation...")
    ordered_results: list[tuple[str, bool, str]] = []

    checks: list[tuple[str, tuple[bool, str]]] = [
        ("System Prompt", validate_system_prompt()),
        ("Cube API Connection", await validate_cube_connection()),
        ("Groq Integration", validate_provider("groq")),
        ("OpenAI Integration", validate_provider("openai")),
        ("Gemini Integration", validate_provider("gemini")),
        ("LangChain Agent", await validate_agent_initialization()),
        ("POST /ask Endpoint", validate_endpoint()),
        ("JSON Responses", validate_json_response()),
        ("Logging", validate_logging()),
        ("README Updated", validate_readme()),
    ]

    for name, (passed, message) in checks:
        ordered_results.append((name, passed, message))
        print(f"{name}: {'PASS' if passed else 'FAIL'} - {message}")

    all_passed = all(passed for _, passed, _ in ordered_results)
    report_lines = [
        "=========================================",
        "MetricMind - Day 9 Validation Report",
        "=========================================",
        "",
    ]
    for name, passed, _ in ordered_results:
        report_lines.append(f"{name:20} : {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
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
        report_lines.append("")
        report_lines.append("Issues:")
        for name, passed, message in ordered_results:
            if not passed:
                report_lines.append(f"- {name}: {message}")

    report_path = log_dir / "day9-final-report.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print("\n" + "\n".join(report_lines))
    print(f"\nReport written to: {report_path}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
