"""Explain endpoint - POST /explain for AI root-cause analysis of business metrics."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.explain.explain_agent import ExplainAgent
from app.models.schemas import ExplainRequest, ExplainResponse

logger = logging.getLogger("metricmind.api.explain")

router = APIRouter(tags=["Explain"])


@router.post("/explain", response_model=ExplainResponse)
async def explain_question(request: ExplainRequest) -> ExplainResponse:
    """
    Analyze a "Why?" business question and return a structured, evidence-based
    root-cause analysis.

    The Explain Results Engine retrieves Cube API data (via Cube.dev), compares the current vs.
    prior period, identifies contributing metrics, produces root-cause findings,
    computes a confidence score, and proposes business recommendations.

    Example:
        {"question": "Why did European margin decrease?"}
    """
    start = time.perf_counter()
    question = (request.question or "").strip()

    if not question:
        logger.warning("Empty explain request rejected")
        raise HTTPException(status_code=400, detail="Question cannot be empty")

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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Explain engine runtime failure for %s", question)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled explain error for %s", question)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "Explain response: question=%s confidence=%s reasons=%d recs=%d time_ms=%.1f",
        question,
        payload.get("confidence"),
        len(payload.get("possible_reasons", [])),
        len(payload.get("recommendations", [])),
        duration_ms,
    )
    return ExplainResponse(**payload)
