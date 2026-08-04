"""Governance Logger — structured JSONL to backend/logs/governance_events.jsonl."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("metricmind.governance.logger")


class GovernanceLogger:
    """Append-only structured logging for all governance decisions + traces."""

    FILENAME = "governance_events.jsonl"

    def __init__(self, log_dir: Path | None = None) -> None:
        self.log_dir = log_dir or (Path(__file__).resolve().parents[2] / "logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / self.FILENAME

    # ------------------------------------------------------------------
    # Public writers
    # ------------------------------------------------------------------
    def write_policy_decision(
        self,
        result: Any,
        *,
        route: str | None = None,
        validation_duration_ms: float = 0.0,
    ) -> bool:
        event: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "event": "policy_decision",
            "route": route,
            "question": getattr(result, "question", None),
            "allowed": getattr(result, "allowed", False),
            "block_code": None,
            "block_reason": None,
            "reasons": [],
            "suggested_filters": [],
            "validation_duration_ms": round(validation_duration_ms, 2),
        }
        violation = getattr(result, "violation", None)
        if violation is not None:
            event["block_code"] = getattr(violation, "code", None)
            event["block_reason"] = getattr(violation, "message", None)
            event["reasons"] = list(getattr(violation, "reasons", []) or [])
            event["suggested_filters"] = list(getattr(violation, "suggested_filters", []) or [])
        return self._append(event)

    def write_cube_trace(
        self,
        *,
        question: str,
        route: str | None,
        cube_trace: dict[str, Any],
    ) -> bool:
        event = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "event": "cube_trace",
            "question": question,
            "route": route,
            "cube_endpoint": cube_trace.get("endpoint"),
            "execution_time_ms": cube_trace.get("execution_time_ms"),
            "response_status": cube_trace.get("response_status"),
            "response_size_bytes": cube_trace.get("response_size_bytes"),
        }
        return self._append(event)

    def write_error(
        self,
        *,
        question: str,
        route: str | None,
        error_type: str,
        detail: str,
    ) -> bool:
        event = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "event": "error",
            "question": question,
            "route": route,
            "error_type": error_type,
            "detail": detail,
        }
        return self._append(event)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _append(self, event: dict[str, Any]) -> bool:
        try:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, default=str, ensure_ascii=False) + "\n")
            return True
        except Exception as exc:
            logger.warning("Failed to write governance log: %s", exc)
            return False
