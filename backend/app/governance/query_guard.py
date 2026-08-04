"""Query Guard — enforces "Only Cube API Allowed".

Wraps downstream calls (LangChain agent, Cube API) and:
  * refuses to proceed if SecurityValidator rejected the question;
  * records Cube API metadata for frontend transparency (View API / View JSON);
  * never invokes SQL directly — no engine.execute(), no raw db drivers used here.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CubeAPITrace:
    """Structured trace that the frontend displays via View API / View JSON."""

    endpoint: str
    method: str
    request_payload: dict[str, Any] = field(default_factory=dict)
    query_parameters: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    response_status: int = 0
    response_size_bytes: int = 0
    response_json: dict[str, Any] | None = None

    def for_view_api(self) -> dict[str, Any]:
        payload = {
            "endpoint": self.endpoint,
            "method": self.method,
            "request_payload": self._redact(self.request_payload),
            "query_parameters": self._redact(self.query_parameters),
            "execution_time_ms": round(self.execution_time_ms, 2),
            "response_status": self.response_status,
            "response_size_bytes": self.response_size_bytes,
        }
        return payload

    def for_view_json(self) -> dict[str, Any]:
        if self.response_json is None:
            return {}
        return self._redact(self.response_json)

    @staticmethod
    def _redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                k: ("<redacted>" if any(secret in k.lower()
                                         for secret in ("token", "secret", "key", "auth", "password", "cookie"))
                        else CubeAPITrace._redact(v))
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [CubeAPITrace._redact(v) for v in value]
        return value


class QueryGuard:
    """Ensures:
      * the question passed SecurityValidator;
      * a CubeAPITrace is always recorded;
      * caller provides pre-fetched Cube JSON (this class does no DB work).
    """

    def __init__(self) -> None:
        self._trace: CubeAPITrace | None = None

    # ------------------------------------------------------------------
    # Context manager-style trace helpers — caller provides Cube payload
    # ------------------------------------------------------------------
    def begin_trace(
        self,
        endpoint: str,
        method: str = "POST",
        query_parameters: dict[str, Any] | None = None,
        request_payload: dict[str, Any] | None = None,
    ) -> None:
        self._trace = CubeAPITrace(
            endpoint=endpoint,
            method=method,
            request_payload=dict(request_payload or {}),
            query_parameters=dict(query_parameters or {}),
        )

    def complete_trace(
        self,
        response_json: dict[str, Any] | None,
        *,
        status: int = 200,
        started_at: float | None = None,
    ) -> CubeAPITrace:
        if self._trace is None:
            self._trace = CubeAPITrace(endpoint="/unknown", method="UNKNOWN")
        trace = self._trace
        if started_at is not None:
            trace.execution_time_ms = (time.perf_counter() - started_at) * 1000
        trace.response_status = status
        trace.response_json = response_json or {}
        try:
            import json
            trace.response_size_bytes = len(json.dumps(response_json or {}))
        except Exception:
            trace.response_size_bytes = 0
        return trace

    def extract_for_response(self) -> dict[str, Any]:
        """Serialize the last trace for the HTTP response body (for transparency UI)."""
        if self._trace is None:
            return {}
        return {
            "cube_trace": self._trace.for_view_api(),
            "cube_json": self._trace.for_view_json(),
        }

    @staticmethod
    def dict_from_trace(trace: CubeAPITrace) -> dict[str, Any]:
        return asdict(trace)
