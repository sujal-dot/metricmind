"""Orchestrate the semantic search and natural language analytics pipeline."""
import logging
import time
from typing import Any, Dict, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.semantic.intent_detector import IntentDetector, UserIntent
from app.semantic.query_parser import QueryParser
from app.semantic.response_formatter import FormattedResult, ResponseFormatter
from app.agents.cube_client import CubeClient
from app.agents.llm_factory import LLMFactory
from app.config.settings import settings

logger = logging.getLogger("metricmind.semantic.router")


EXPLANATION_PROMPT_TEMPLATE = """
You are a Business Intelligence Analyst.

Rules:
- Use only the provided Cube.dev results.
- Never generate SQL.
- Never mention PostgreSQL access.
- Do not invent values.
- If there is no data, say so clearly.

Question: {question}
Summary: {summary}
Key insights: {key_insights}
Cube rows: {cube_rows}

Write a concise business explanation.
"""


class SemanticRouter:
    """Run semantic detection, query routing, Cube execution, and explanation."""

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        llm: BaseChatModel | Any = None,
        cube_client: CubeClient | Any = None,
        intent_detector: IntentDetector | None = None,
        query_parser: QueryParser | None = None,
        response_formatter: ResponseFormatter | None = None,
    ):
        self.provider = llm_provider or settings.llm_provider
        self.llm: BaseChatModel = llm or LLMFactory.create_llm(provider=self.provider)
        self.intent_detector = intent_detector or IntentDetector()
        self.query_parser = query_parser or QueryParser()
        self.response_formatter = response_formatter or ResponseFormatter()
        self.cube_client = cube_client or CubeClient()
        logger.info("SemanticRouter initialized with %s as LLM provider", self.provider)

    async def process(self, question: str) -> Dict[str, Any]:
        """Execute the semantic search pipeline."""
        start_time = time.perf_counter()
        question = question.strip()
        if not question:
            raise ValueError("Invalid user request: question cannot be empty")

        logger.info("Starting pipeline for question: %s", question)
        results: Dict[str, Any] = {"question": question, "provider": self.provider}

        try:
            intent: UserIntent = self.intent_detector.detect(question)
            results["intent"] = intent.model_dump()

            cube_query = self.query_parser.parse(intent)
            results["cube_query"] = cube_query

            cube_response = await self.cube_client.load(cube_query)
            self._validate_cube_response(cube_response)
            results["cube_response"] = cube_response

            formatted: FormattedResult = self.response_formatter.format(cube_response)
            results["formatted_response"] = formatted.model_dump()

            explanation = await self._generate_explanation(
                question=question,
                formatted=formatted,
            )
            results["explanation"] = explanation
            logger.info("Generated explanation: %s", explanation)

        except ValueError:
            logger.exception("Semantic validation failed for question: %s", question)
            raise
        except Exception as exc:
            logger.exception("Pipeline failed for question: %s", question)
            raise RuntimeError(f"Semantic search pipeline failed: {exc}") from exc
        duration = time.perf_counter() - start_time
        logger.info("Pipeline completed in %.4f seconds", duration)

        return results

    def _validate_cube_response(self, cube_response: Dict[str, Any]) -> None:
        if not isinstance(cube_response, dict):
            raise ValueError("Invalid Cube API response: expected JSON object")
        if "error" in cube_response:
            raise ValueError(f"Cube API returned an error: {cube_response['error']}")
        if "data" not in cube_response and "results" not in cube_response:
            raise ValueError("Invalid Cube API response: missing data or results field")

    async def _generate_explanation(self, question: str, formatted: FormattedResult) -> str:
        prompt = EXPLANATION_PROMPT_TEMPLATE.format(
            question=question,
            summary=formatted.summary,
            key_insights="; ".join(formatted.key_insights),
            cube_rows=str(formatted.data_points[:10]),
        )
        result = await self.llm.ainvoke(
            [
                SystemMessage(content="You explain Cube.dev analytics results in business language."),
                HumanMessage(content=prompt),
            ]
        )
        explanation = self._extract_text(result).strip()
        if not explanation:
            raise RuntimeError("LLM returned an empty explanation")
        if "select " in explanation.lower() or " from " in explanation.lower():
            raise RuntimeError("LLM explanation must not include SQL")
        return explanation

    @staticmethod
    def _extract_text(message: Any) -> str:
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            return "\n".join(part for part in parts if part)
        return str(content)
