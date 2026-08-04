"""Policy Engine — the single public entrypoint for governance checks.

Other services should call PolicyEngine.validate(question) and raise/redirect
based on the returned PolicyResult. This central module composes:

  SecurityValidator.validate() → SQL / expensive checks
  QueryGuard                  → Cube-only enforcement & trace recording
  GovernanceLogger            → writes JSONL to backend/logs/
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.governance.governance_logger import GovernanceLogger
from app.governance.query_guard import CubeAPITrace, QueryGuard
from app.governance.security_validator import SecurityDecision, SecurityValidator


@dataclass
class PolicyViolation:
    code: str  # sql_injection | sql_request | expensive | unsupported
    message: str
    reasons: list[str] = field(default_factory=list)
    suggested_filters: list[str] = field(default_factory=list)


@dataclass
class PolicyResult:
    question: str
    allowed: bool
    decision: SecurityDecision | None = None
    violation: PolicyViolation | None = None
    cube_trace: dict[str, Any] | None = None
    cube_json: dict[str, Any] | None = None
    logged: bool = False

    def as_http_error(self) -> dict[str, Any]:
        if self.allowed or not self.violation:
            return {}
        return {
            "detail": self.violation.message,
            "block_code": self.violation.code,
            "reasons": self.violation.reasons,
            "suggested_filters": self.violation.suggested_filters,
        }


class PolicyEngine:
    """Unified governance entrypoint.

    Usage:
        engine = PolicyEngine()
        result = engine.validate("Why did revenue drop?")
        if not result.allowed:
            raise HTTPException(403, detail=result.as_http_error()["detail"])

        # Then, when you have your Cube JSON payload:
        engine.attach_cube_trace(result, payload, endpoint="/cubejs-api/v1/load")
    """

    def __init__(self) -> None:
        self.security_validator = SecurityValidator()
        self.query_guard = QueryGuard()
        self.logger = GovernanceLogger()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate(self, question: str, *, route: str | None = None) -> PolicyResult:
        question = (question or "").strip()
        started_at = time.perf_counter()
        decision = self.security_validator.validate(question)

        if decision.allowed:
            result = PolicyResult(
                question=question,
                allowed=True,
                decision=decision,
                cube_trace=None,
                cube_json=None,
            )
        else:
            reasons: list[str] = []
            if decision.sql_result is not None:
                reasons.extend(decision.sql_result.matched_injection_reasons)
                reasons.extend(decision.sql_result.matched_request_reasons)
            if decision.expensive_result is not None:
                reasons.extend(decision.expensive_result.matched_reasons)
            violation = PolicyViolation(
                code=decision.block_code or "sql_injection",
                message=decision.human_message,
                reasons=reasons,
                suggested_filters=list(decision.suggested_filters),
            )
            result = PolicyResult(
                question=question,
                allowed=False,
                decision=decision,
                violation=violation,
            )

        duration_ms = (time.perf_counter() - started_at) * 1000
        logged = self.logger.write_policy_decision(
            result,
            route=route,
            validation_duration_ms=duration_ms,
        )
        result.logged = logged
        return result

    def attach_cube_trace(
        self,
        result: PolicyResult,
        cube_json: dict[str, Any] | None,
        *,
        endpoint: str = "/cubejs-api/v1/load",
        method: str = "POST",
        query_parameters: dict[str, Any] | None = None,
        request_payload: dict[str, Any] | None = None,
        started_at: float | None = None,
        status: int = 200,
    ) -> CubeAPITrace:
        self.query_guard.begin_trace(
            endpoint=endpoint,
            method=method,
            query_parameters=query_parameters,
            request_payload=request_payload,
        )
        trace = self.query_guard.complete_trace(
            cube_json, status=status, started_at=started_at
        )
        result.cube_trace = self.query_guard._trace.for_view_api()  # type: ignore[union-attr]
        result.cube_json = self.query_guard._trace.for_view_json()  # type: ignore[union-attr]
        return trace
