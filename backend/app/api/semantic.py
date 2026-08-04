"""Semantic Search and Natural Language Analytics API endpoint."""
import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user, require_csrf
from app.governance.policy_engine import PolicyEngine
from app.models.schemas import SemanticSearchRequest, SemanticSearchResponse
from app.semantic.semantic_router import SemanticRouter

logger = logging.getLogger("metricmind.api.semantic")
router = APIRouter()

_POLICY = PolicyEngine()


def _attach_transparency(payload: dict, question: str, cube_response: dict | None) -> None:
    cube_response = cube_response or payload.get("cube_response") or {}
    trace = {
        "endpoint": "/cubejs-api/v1/load",
        "method": "POST",
        "request_payload": {"question": question},
        "query_parameters": {"route": "/semantic-search"},
        "execution_time_ms": 0,
        "response_status": 200,
        "response_size_bytes": 0,
    }
    try:
        import json
        trace["response_size_bytes"] = len(json.dumps(cube_response or {}))
    except Exception:
        pass
    payload.setdefault("cube_trace", trace)
    payload.setdefault("cube_json", cube_response or {})
    try:
        _POLICY.logger.write_cube_trace(question=question, route="/semantic-search", cube_trace=trace)
    except Exception:
        pass


@router.post("/semantic-search", response_model=SemanticSearchResponse, tags=["Semantic Search"])
async def semantic_search(
    request: SemanticSearchRequest,
    _: dict = Depends(get_current_user),
    __: None = Depends(require_csrf),
):
    """Process natural language question and return analytics insights via semantic search pipeline.

    Questions pass through the Day 16 Governance Policy Engine (SQL injection /
    raw-SQL / expensive query guard) before the semantic layer, and all answers route
    exclusively through the Cube.dev Semantic API — never via direct SQL.
    """
    logger.info("Received semantic search request: %s", request.question)
    question = (request.question or "").strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Invalid user request: question cannot be empty",
        )
    policy_result = _POLICY.validate(question, route="/semantic-search")
    if not policy_result.allowed:
        payload = policy_result.as_http_error()
        detail = payload.get("detail") or "Governance policy blocked this request"
        logger.warning("Governance blocked /semantic-search: %s", detail)
        raise HTTPException(status_code=403, detail=detail)
    try:
        start = time.perf_counter()
        semantic_router = SemanticRouter()
        pipeline_result = await semantic_router.process(request.question)
        logger.info("Semantic search pipeline completed")
        if isinstance(pipeline_result, dict):
            result_dict = dict(pipeline_result)
        else:
            result_dict = dict(pipeline_result.model_dump())
        cube_body = result_dict.get("cube_response")
        _attach_transparency(result_dict, question, cube_body)
        response = SemanticSearchResponse(**result_dict)
        if response.cube_trace is not None:
            response.cube_trace["execution_time_ms"] = round(
                (time.perf_counter() - start) * 1000, 2
            )
        return response
    except ValueError as exc:
        logger.warning("Invalid semantic search request: %s", exc)
        _POLICY.logger.write_error(
            question=question,
            route="/semantic-search",
            error_type="ValueError",
            detail=str(exc),
        )
        raise HTTPException(status_code=400, detail="Invalid request") from exc
    except RuntimeError as exc:
        logger.exception("Semantic search runtime failure")
        _POLICY.logger.write_error(
            question=question,
            route="/semantic-search",
            error_type="RuntimeError",
            detail=str(exc),
        )
        raise HTTPException(status_code=503, detail="Analytics service unavailable") from exc
    except Exception as exc:
        logger.exception("Semantic search failed")
        _POLICY.logger.write_error(
            question=question,
            route="/semantic-search",
            error_type="Exception",
            detail=str(exc),
        )
        raise HTTPException(status_code=500, detail="Internal server error") from exc
