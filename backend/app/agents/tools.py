import json
import logging
from typing import Any, Dict

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from app.agents.cube_client import CubeClient

logger = logging.getLogger("metricmind.agents.tools")


class CubeQueryInput(BaseModel):
    query: Dict[str, Any] | None = Field(
        None,
        description="Optional wrapped Cube.dev query JSON object.",
    )
    measures: list[str] | None = Field(None, description="Cube measure names to query.")
    dimensions: list[str] | None = Field(None, description="Cube dimension names to group by.")
    timeDimensions: list[Dict[str, Any]] | None = Field(None, description="Cube time dimension filters.")
    filters: list[Dict[str, Any]] | None = Field(None, description="Cube filters.")
    limit: int | None = Field(None, description="Maximum number of rows to return.")
    order: Dict[str, Any] | None = Field(None, description="Cube order clause.")

    class Config:
        extra = "allow"


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
        async def _run_cube_query(**kwargs: Any) -> str:
            query = kwargs.pop("query", None)
            if query is None:
                query = {key: value for key, value in kwargs.items() if value is not None}
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
