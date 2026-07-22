import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.routes import router as routes_router
from app.api.sales import router as sales_router
from app.agents.bi_agent import BIAgent
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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_router, tags=["core"])
app.include_router(sales_router, prefix="/api/v1", tags=["sales"])
app.include_router(metrics_router, prefix="/api/v1", tags=["metrics"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])


@app.post("/ask", response_model=BIAnswerResponse, tags=["BI Agent"])
async def ask_question(request: BIQuestionRequest):
    """
    Ask a natural language business question to the BI Agent.
    The agent will use Cube.dev to get data and return a business insight.
    """
    try:
        agent = BIAgent()
        return await agent.ask(request.question)
    except ValueError as exc:
        logger.warning("Invalid BI request: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("BI agent runtime failure")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to process question")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
