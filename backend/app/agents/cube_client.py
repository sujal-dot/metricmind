import logging
from typing import Any

import httpx

from app.config.settings import settings

logger = logging.getLogger("metricmind.agents.cube_client")


class CubeClient:
    def __init__(self, api_url: str | None = None, api_token: str | None = None):
        self.api_url = (api_url or settings.cube_api_url).rstrip("/")
        self.api_token = api_token or settings.cube_api_token
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.api_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(method, url, json=json_body, headers=self.headers)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Cube.dev returned a non-object JSON response")
                return payload
        except httpx.TimeoutException as exc:
            logger.error("Cube.dev request timed out for %s %s", method, url)
            raise RuntimeError("Cube.dev request timed out") from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Cube.dev API returned HTTP %s for %s: %s",
                exc.response.status_code,
                url,
                exc.response.text,
            )
            raise RuntimeError(
                f"Cube.dev API error: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Cube.dev connection error for %s: %s", url, exc)
            raise RuntimeError("Cube.dev is unavailable") from exc
        except ValueError as exc:
            logger.error("Cube.dev returned invalid JSON for %s: %s", url, exc)
            raise RuntimeError("Cube.dev returned an invalid response") from exc

    @staticmethod
    def _normalize_query(query: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(query, dict):
            return query
        q = dict(query)
        time_dims = q.get("timeDimensions")
        if isinstance(time_dims, list):
            normalized_tds = []
            for td in time_dims:
                if isinstance(td, dict):
                    td_copy = dict(td)
                    if td_copy.get("dimension") == "FactSales.createdAt":
                        td_copy["dimension"] = "DimDate.fullDate"

                    dr = td_copy.get("dateRange")
                    if isinstance(dr, str):
                        dr_clean = dr.strip()
                        if dr_clean.isdigit() and len(dr_clean) == 4:
                            td_copy["dateRange"] = [f"{dr_clean}-01-01", f"{dr_clean}-12-31"]
                    elif isinstance(dr, list):
                        if len(dr) == 1 and isinstance(dr[0], str) and dr[0].strip().isdigit() and len(dr[0].strip()) == 4:
                            yr = dr[0].strip()
                            td_copy["dateRange"] = [f"{yr}-01-01", f"{yr}-12-31"]
                        elif len(dr) == 2 and isinstance(dr[0], str) and isinstance(dr[1], str):
                            d1 = dr[0].strip()
                            d2 = dr[1].strip()
                            if d1.isdigit() and len(d1) == 4:
                                d1 = f"{d1}-01-01"
                            if d2.isdigit() and len(d2) == 4:
                                d2 = f"{d2}-12-31"
                            td_copy["dateRange"] = [d1, d2]
                    normalized_tds.append(td_copy)
                else:
                    normalized_tds.append(td)
            q["timeDimensions"] = normalized_tds
        return q

    async def load(self, query: dict[str, Any]) -> dict[str, Any]:
        normalized_query = self._normalize_query(query)
        logger.info("Sending Cube.dev load query: %s", normalized_query)
        result = await self._request("POST", "load", json_body={"query": normalized_query})
        logger.info("Received Cube.dev load response with keys: %s", list(result.keys()))
        return result

    async def meta(self) -> dict[str, Any]:
        logger.info("Fetching metadata from Cube.dev")
        result = await self._request("GET", "meta")
        logger.info("Successfully retrieved Cube.dev metadata")
        return result

    async def check_connection(self) -> bool:
        meta = await self.meta()
        return "cubes" in meta
