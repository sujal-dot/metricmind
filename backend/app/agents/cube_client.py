import logging
from typing import Any, Dict, Optional

import httpx

from app.config.settings import settings

logger = logging.getLogger("metricmind.agents.cube_client")


class CubeClient:
    def __init__(self, api_url: Optional[str] = None, api_token: Optional[str] = None):
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
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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

    async def load(self, query: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Sending Cube.dev load query: %s", query)
        result = await self._request("POST", "load", json_body={"query": query})
        logger.info("Received Cube.dev load response with keys: %s", list(result.keys()))
        return result

    async def meta(self) -> Dict[str, Any]:
        logger.info("Fetching metadata from Cube.dev")
        result = await self._request("GET", "meta")
        logger.info("Successfully retrieved Cube.dev metadata")
        return result

    async def check_connection(self) -> bool:
        meta = await self.meta()
        return "cubes" in meta
