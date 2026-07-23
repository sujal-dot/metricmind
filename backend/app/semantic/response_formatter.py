"""Format Cube.dev API responses for semantic explanation generation."""
import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field

logger = logging.getLogger("metricmind.semantic.formatter")


class FormattedResult(BaseModel):
    """Structured data passed into the explanation step."""

    summary: str
    row_count: int
    has_data: bool
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)


class ResponseFormatter:
    """Normalize Cube responses and derive simple business observations."""

    def format(self, cube_response: Dict[str, Any]) -> FormattedResult:
        logger.info("Formatting Cube response for explanation step")
        data_points = self._extract_rows(cube_response)
        row_count = len(data_points)
        has_data = row_count > 0

        if has_data:
            summary = f"Cube returned {row_count} row{'s' if row_count != 1 else ''}."
        else:
            summary = "Cube returned no rows for this query."

        result = FormattedResult(
            summary=summary,
            row_count=row_count,
            has_data=has_data,
            data_points=data_points,
            key_insights=self._extract_insights(data_points),
        )
        logger.info("Formatted result summary: %s", result.summary)
        return result

    def _extract_rows(self, cube_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        if isinstance(cube_response.get("data"), list):
            return cube_response["data"]

        if isinstance(cube_response.get("results"), list) and cube_response["results"]:
            first = cube_response["results"][0]
            if isinstance(first, dict) and isinstance(first.get("data"), list):
                return first["data"]

        return []

    def _extract_insights(self, data_points: List[Dict[str, Any]]) -> List[str]:
        if not data_points:
            return ["No data was available for the requested query."]

        insights = [f"Retrieved {len(data_points)} record{'s' if len(data_points) != 1 else ''}."]
        sample_row = data_points[0]
        if sample_row:
            keys = ", ".join(sample_row.keys())
            insights.append(f"Available fields: {keys}.")
        return insights
