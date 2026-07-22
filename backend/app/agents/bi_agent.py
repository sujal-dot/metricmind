import logging
import time
from typing import Any, Dict, Literal, Sequence

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.agents.prompts import BI_ANALYST_SYSTEM_PROMPT, FINAL_ANSWER_INSTRUCTION
from app.agents.llm_factory import LLMFactory
from app.agents.tools import get_all_tools
from app.config.settings import settings

logger = logging.getLogger("metricmind.agents.bi_agent")


class BIAgent:
    def __init__(
        self,
        llm_provider: Literal["groq", "openai", "gemini"] = None,
        llm: Any = None,
        tools: Sequence[BaseTool] | None = None,
    ):
        self.provider = llm_provider or settings.llm_provider
        self.llm = llm or LLMFactory.create_llm(provider=self.provider)
        self.tools = list(tools or get_all_tools())
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        logger.info("BI Agent initialized successfully")

    async def ask(self, question: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        question = question.strip()
        if not question:
            raise ValueError("Invalid user request: question cannot be empty")

        logger.info("User question: %s", question)
        logger.info("Selected LLM provider: %s", self.provider)

        try:
            planning_messages = [
                SystemMessage(content=BI_ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=question),
            ]
            planner_response = await self.llm_with_tools.ainvoke(planning_messages)

            if not getattr(planner_response, "tool_calls", None):
                raise ValueError(
                    "Invalid user request: no supported Cube.dev metric or dimension could be identified."
                )

            tool_messages = []
            for tool_call in planner_response.tool_calls:
                tool_name = tool_call["name"]
                tool = self.tool_map.get(tool_name)
                if tool is None:
                    raise ValueError(f"Unsupported tool requested by agent: {tool_name}")
                tool_result = await tool.ainvoke(tool_call["args"])
                tool_messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )

            final_messages = [
                SystemMessage(content=BI_ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=question),
                planner_response,
                *tool_messages,
                HumanMessage(content=FINAL_ANSWER_INSTRUCTION),
            ]
            final_response = await self.llm.ainvoke(final_messages)
            answer = self._extract_text(final_response)
            if not answer.strip():
                raise RuntimeError("LLM returned an empty answer")

            duration = time.perf_counter() - start_time
            logger.info("Agent response generated in %.4fs", duration)
            logger.info("Agent answer: %s", answer)

            return {
                "question": question,
                "answer": answer,
                "source": "Cube API",
                "provider": self.provider,
            }
        except Exception:
            logger.exception("Error processing question: %s", question)
            raise

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
