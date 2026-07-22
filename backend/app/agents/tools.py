import json
import logging
from typing import Any, Dict, Type

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from app.agents.cube_client import CubeClient

logger = logging.getLogger("metricmind.agents.tools")


class CubeQueryInput(BaseModel):
    query: Dict[str, Any] = Field(
        ...,
        description="Cube.dev query JSON object with measures, dimensions, timeDimensions, filters, limit, and order.",
    )


class CubeQueryTool:
    name = "cube_query"
    description = (
        "Query Cube.dev for analytics. Always use this tool before answering a supported business question. "
        "Example: {\"measures\": [\"FactSales.revenue\"], \"timeDimensions\": [{\"dimension\": \"DimDate.fullDate\", \"dateRange\": \"last month\"}]}"
    )

    def __init__(self, client: CubeClient | None = None):
        self.client = client or CubeClient()

    async def arun(self, query: Dict[str, Any]) -> str:
        try:
            result = await self.client.load(query)
            return json.dumps(result, indent=2)
        except Exception as exc:
            logger.error("Error executing Cube query tool: %s", exc)
            return json.dumps({"error": str(exc)})

    def as_langchain_tool(self) -> BaseTool:
        async def _run_cube_query(query: Dict[str, Any]) -> str:
            return await self.arun(query)

        return StructuredTool.from_function(
            coroutine=_run_cube_query,
            name=self.name,
            description=self.description,
            args_schema=CubeQueryInput,
        )


def get_all_tools(client: CubeClient | None = None) -> list[BaseTool]:
    query_tool = CubeQueryTool(client=client)
    return [query_tool.as_langchain_tool()]
