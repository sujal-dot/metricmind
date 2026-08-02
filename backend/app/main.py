import logging
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.routes import router as routes_router
from app.api.sales import router as sales_router
from app.api.analytics import router as analytics_router
from app.api.semantic import router as semantic_router
from app.api.explain import router as explain_router
from app.api.governance import router as governance_router
from app.api.conversations import router as conversations_router
from app.api.users import router as users_router
from app.auth.dependencies import get_current_user, require_csrf
from app.agents.bi_agent import BIAgent
from app.config.settings import settings
from app.governance.policy_engine import PolicyEngine
from app.models.schemas import BIQuestionRequest, BIAnswerResponse
from app.services.database import check_database_connection

BASE_DIR = Path(__file__).resolve().parents[2]
log_dir = BASE_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "backend.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("metricmind.api")

app = FastAPI(
    title="MetricMind API",
    description="Agentic Business Intelligence Platform API",
    version="0.1.0",
    docs_url="/docs" if settings.effective_docs_enabled else None,
    redoc_url="/redoc" if settings.effective_docs_enabled else None,
    openapi_url="/openapi.json" if settings.effective_docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", settings.csrf_header_name],
)

app.include_router(routes_router, tags=["core"])
app.include_router(auth_router)
app.include_router(sales_router, prefix="/api/v1", tags=["sales"])
app.include_router(metrics_router, prefix="/api/v1", tags=["metrics"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(semantic_router)
app.include_router(explain_router)
app.include_router(governance_router)
app.include_router(conversations_router)
app.include_router(users_router)

_POLICY = PolicyEngine()


def _attach_transparency(payload: dict, question: str, route: str, cube_response: dict | None) -> None:
    """Attach cube_trace + cube_json payloads for the frontend View API / View JSON buttons."""
    cube_response = cube_response or payload.get("cube_response") or {}
    request_payload = {"question": question}
    trace = {
        "endpoint": "/cubejs-api/v1/load",
        "method": "POST",
        "request_payload": request_payload,
        "query_parameters": {"route": route},
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
        _POLICY.logger.write_cube_trace(
            question=question,
            route=route,
            cube_trace=trace,
        )
    except Exception:
        pass


@app.post("/ask", response_model=BIAnswerResponse, tags=["BI Agent"])
async def ask_question(
    request: BIQuestionRequest,
    _: dict = Depends(get_current_user),
    __: None = Depends(require_csrf),
):
    """
    Ask a natural language business question to the BI Agent.
    The question first passes through the Day 16 Governance Policy Engine
    (SQL / expensive query blocking). Analytics are then answered via the
    Cube.dev Semantic API — direct SQL or database access is never used.
    """
    question = (request.question or "").strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Invalid user request: question cannot be empty",
        )
    policy_result = _POLICY.validate(question, route="/ask")
    if not policy_result.allowed:
        payload = policy_result.as_http_error()
        detail = payload.get("detail") or "Governance policy blocked this request"
        logger.warning("Governance blocked /ask: %s", detail)
        raise HTTPException(status_code=403, detail=detail)
    try:
        agent = BIAgent()
        answer = await agent.ask(question)
        answer_dict = answer if isinstance(answer, dict) else answer.model_dump()
        cube_body = answer_dict.get("cube_response") if isinstance(answer_dict, dict) else None
        _attach_transparency(answer_dict, question, "/ask", cube_body)
        return BIAnswerResponse(**answer_dict)
    except ValueError as exc:
        logger.warning("Invalid BI request: %s", exc)
        _POLICY.logger.write_error(question=question, route="/ask", error_type="ValueError", detail=str(exc))
        raise HTTPException(status_code=400, detail="Invalid request") from exc
    except RuntimeError as exc:
        logger.exception("BI agent runtime failure")
        _POLICY.logger.write_error(question=question, route="/ask", error_type="RuntimeError", detail=str(exc))
        raise HTTPException(status_code=503, detail="Analytics service unavailable") from exc
    except Exception as exc:
        logger.exception("Failed to process question")
        _POLICY.logger.write_error(question=question, route="/ask", error_type="Exception", detail=str(exc))
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Incoming request: %s %s", request.method, request.url.path)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled exception for %s %s: %s", request.method, request.url.path, exc)
        raise
    duration = time.perf_counter() - start
    logger.info("Completed %s %s in %.4fs with status %s", request.method, request.url.path, duration, response.status_code)
    return response


@app.on_event("startup")
def startup_event() -> None:
    logger.info("MetricMind backend starting up")
    if check_database_connection():
        logger.info("PostgreSQL connection successful")
        try:
            from app.services.migrations import run_migrations_upgrade
            run_migrations_upgrade()
        except Exception:
            logger.exception("Failed to run migrations on startup")
    else:
        logger.error("PostgreSQL connection failed")


@app.exception_handler(404)
async def not_found_handler(_: Request, exc: Exception):
    logger.warning("Resource not found: %s", exc)
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.warning("Validation error: %s", exc)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(_: Request, exc: SQLAlchemyError):
    logger.exception("Database error: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "Database unavailable"})


@app.exception_handler(Exception)
async def general_exception_handler(_: Request, exc: Exception):
    logger.exception("Unexpected exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
