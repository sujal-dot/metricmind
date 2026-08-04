"""Governance endpoints for the transparency UI.

POST /governance/validate - runs PolicyEngine on one question (used by the
    frontend ChatWindow to block policy violations *before* sending a question
    to the actual agent endpoints).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_csrf
from app.governance.policy_engine import PolicyEngine
from app.models.schemas import (
    GovernanceValidationRequest,
    GovernanceValidationResponse,
    SecurityDecisionSchema,
)

logger = logging.getLogger("metricmind.api.governance")

router = APIRouter(prefix="/governance", tags=["Governance"])

_POLICY = PolicyEngine()


def _decision_to_schema(
    question: str,
    result: Any,
) -> SecurityDecisionSchema:
    decision = getattr(result, "decision", None)
    sql_res = getattr(decision, "sql_result", None) if decision is not None else None
    exp_res = getattr(decision, "expensive_result", None) if decision is not None else None

    reasons: list[str] = []
    if sql_res is not None:
        reasons.extend(sql_res.matched_injection_reasons or [])
        reasons.extend(sql_res.matched_request_reasons or [])
    if exp_res is not None:
        reasons.extend(getattr(exp_res, "matched_reasons", []) or [])
    violation = getattr(result, "violation", None)
    if violation is not None:
        extra = getattr(violation, "reasons", None) or []
        for r in extra:
            if r not in reasons:
                reasons.append(r)

    return SecurityDecisionSchema(
        allowed=bool(getattr(result, "allowed", False)),
        block_reason=getattr(decision, "human_message", None) if decision is not None else (
            getattr(violation, "message", None) if violation is not None else None
        ),
        block_code=(
            getattr(decision, "block_code", None) if decision is not None
            else (getattr(violation, "code", None) if violation is not None else None)
        ),
        suggested_filters=list(getattr(decision, "suggested_filters", []) or []),
        has_sql_injection=bool(sql_res and sql_res.is_sql_injection),
        has_sql_request=bool(sql_res and sql_res.is_sql_request),
        is_expensive=bool(exp_res and exp_res.is_expensive),
        matched_reasons=reasons,
    )


@router.post("/validate", response_model=GovernanceValidationResponse)
async def governance_validate(
    request: GovernanceValidationRequest,
    _: dict = Depends(get_current_user),
    __: None = Depends(require_csrf),
) -> GovernanceValidationResponse:
    """
    Validate a user question against the governance policy BEFORE sending it
    to the BI / Explain / Semantic endpoints.

    Returns:
      - whether the question is allowed;
      - block reason / human-readable message;
      - matched detection reasons;
      - suggested filters for over-broad queries.

    Does NOT execute the question itself.
    """
    question = (request.question or "").strip()
    if not question:
        return GovernanceValidationResponse(
            question="",
            decision=SecurityDecisionSchema(
                allowed=False,
                block_reason="Question cannot be empty.",
                block_code="sql_injection",
            ),
        )
    result = _POLICY.validate(question, route=request.route)
    decision_schema = _decision_to_schema(question, result)

    trace: dict[str, Any] | None = None
    json_body: dict[str, Any] | None = None
    if getattr(result, "cube_trace", None):
        trace = result.cube_trace
    if getattr(result, "cube_json", None):
        json_body = result.cube_json

    logger.info(
        "Governance validate: allowed=%s block_code=%s question=%s",
        decision_schema.allowed,
        decision_schema.block_code,
        question[:80],
    )
    return GovernanceValidationResponse(
        question=question,
        decision=decision_schema,
        cube_trace=trace,
        cube_json=json_body,
    )
