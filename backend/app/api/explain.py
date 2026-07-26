"""Explain endpoint - POST /explain for AI root-cause analysis of business metrics."""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.explain.explain_agent import ExplainAgent
from app.governance.policy_engine import PolicyEngine
from app.models.schemas import ExplainRequest, ExplainResponse

logger = logging.getLogger("metricmind.api.explain")

router = APIRouter(tags=["Explain"])

_POLICY = PolicyEngine()


def _attach_transparency(payload: Dict[str, Any], question: str) -> None:
    cube_response = payload.get("cube_json") or {"summary": payload.get("summary", {})}
    trace = {
        "endpoint": "/cubejs-api/v1/load",
        "method": "POST",
        "request_payload": {"question": question},
        "query_parameters": {"route": "/explain"},
        "execution_time_ms": 0,
        "response_status": 200,
        "response_size_bytes": 0,
    }
    try:
        trace["response_size_bytes"] = len(json.dumps(cube_response or {}))
    except Exception:
        pass
    payload.setdefault("cube_trace", trace)
    payload.setdefault("cube_json", cube_response or {})
    try:
        _POLICY.logger.write_cube_trace(question=question, route="/explain", cube_trace=trace)
    except Exception:
        pass


@router.post("/explain", response_model=ExplainResponse)
async def explain_question(request: ExplainRequest) -> ExplainResponse:
    """
    Analyze a "Why?" business question and return a structured, evidence-based
    root-cause analysis.

    The question passes through the Day 16 Governance Policy Engine (SQL /
    expensive-query guard) first; after that, the Explain Results Engine
    retrieves Cube API data (via Cube.dev), compares the current vs. prior
    period, identifies contributing metrics, produces root-cause findings,
    computes a confidence score, and proposes business recommendations. The
    response also embeds cube_trace + cube_json for the frontend View API /
    View JSON transparency buttons.

    Example:
        {"question": "Why did European margin decrease?"}
    """
    start = time.perf_counter()
    question = (request.question or "").strip()

    if not question:
        logger.warning("Empty explain request rejected")
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    policy_result = _POLICY.validate(question, route="/explain")
    if not policy_result.allowed:
        detail = policy_result.as_http_error().get(
            "detail", "Governance policy blocked this request"
        )
        logger.warning("Governance blocked /explain: %s", detail)
        raise HTTPException(status_code=403, detail=detail)

    logger.info("Explain request: %s", question)
    agent = ExplainAgent(use_llm_synthesis=False)

    if not agent.is_supported(question):
        logger.warning("Unsupported explain question: %s", question)
        raise HTTPException(
            status_code=422,
            detail=(
                "This question is not supported for root-cause analysis. "
                "Please rephrase it as a Why? question, e.g. "
                "'Why did European margin decrease?'."
            ),
        )

    try:
        payload: Dict[str, Any] = await agent.explain(question)
    except ValueError as exc:
        logger.warning("Explain engine rejected question: %s -> %s", question, exc)
        _POLICY.logger.write_error(
            question=question, route="/explain", error_type="ValueError", detail=str(exc)
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Explain engine runtime failure for %s", question)
        _POLICY.logger.write_error(
            question=question, route="/explain", error_type="RuntimeError", detail=str(exc)
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled explain error for %s", question)
        _POLICY.logger.write_error(
            question=question, route="/explain", error_type="Exception", detail=str(exc)
        )
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc

    _attach_transparency(payload, question)
    duration_ms = (time.perf_counter() - start) * 1000
    if payload.get("cube_trace") is not None:
        payload["cube_trace"]["execution_time_ms"] = round(duration_ms, 2)

    logger.info(
        "Explain response: question=%s confidence=%s reasons=%d recs=%d time_ms=%.1f",
        question,
        payload.get("confidence"),
        len(payload.get("possible_reasons", [])),
        len(payload.get("recommendations", [])),
        duration_ms,
    )
    return ExplainResponse(**payload)
