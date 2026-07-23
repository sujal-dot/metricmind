"""Semantic Search and Natural Language Analytics API endpoint."""
import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SemanticSearchRequest,
    SemanticSearchResponse
)
from app.semantic.semantic_router import SemanticRouter

logger = logging.getLogger("metricmind.api.semantic")
router = APIRouter()


@router.post("/semantic-search", response_model=SemanticSearchResponse, tags=["Semantic Search"])
async def semantic_search(request: SemanticSearchRequest):
    """Process natural language question and return analytics insights via semantic search pipeline."""
    logger.info("Received semantic search request: %s", request.question)
    try:
        semantic_router = SemanticRouter()
        pipeline_result = await semantic_router.process(request.question)
        logger.info("Semantic search pipeline completed")
        return SemanticSearchResponse(**pipeline_result)
    except ValueError as exc:
        logger.warning("Invalid semantic search request: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Semantic search runtime failure")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Semantic search failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
