# MetricMind Backend

## Overview

This backend exposes a FastAPI service for the MetricMind analytics platform. It connects to the existing PostgreSQL warehouse and exposes REST endpoints for sales, aggregated metrics, a LangChain BI Agent, and a Semantic Search & Natural Language Analytics Pipeline that answers business questions via Cube.dev.

## LangChain BI Agent Architecture

- **BI Agent**: A LangChain agent that uses an LLM to understand natural language questions and uses Cube.dev to retrieve analytics
- **LLM Factory**: Supports Groq, OpenAI, and Gemini LLMs
- **Cube Client**: Connects to the agent to Cube.dev
- **Tools**: Custom LangChain tools for querying Cube.dev
- **Endpoints**: `/ask` (Day 9) and `/semantic-search` (Day 10) for natural language analytics

## Semantic Search Architecture (Day 10)

- **Intent Detector**: Analyzes questions to detect metrics, dimensions, filters, and time ranges
- **Query Parser**: Converts detected intent into valid Cube.dev query syntax
- **Semantic Router**: Orchestrates the complete pipeline
- **Response Formatter**: Structures Cube API responses for LLM consumption
- **Explanation Generator**: Uses LLM to provide business insights from data
- **Endpoint**: `/semantic-search` for semantic search pipeline

## Explain Results Architecture (Day 15)

Pipeline for answering "Why?" questions with evidence-based root-cause analysis:

```
User Question
  ├─► Why-question detection
  ├─► MetricAnalyzer (region / metric / period / direction hints)
  ├─► Cube API snapshot (current vs. prior period)
  ├─► RootCauseAnalyzer  → possible_reasons[]  (evidence-weighted)
  ├─► ConfidenceScorer   → 0–100% + 4 component breakdown
  ├─► RecommendationEngine → top-5 business actions
  └─► (optional) LLM narrative synthesis
       ↓
   POST /explain JSON response
```

Module map:

| File | Purpose |
|---|---|
| `app/explain/metric_analyzer.py` | Why-question detection, region/metric/period/direction hints, builds current vs. prior `MetricSnapshot` from Cube / MetricsService |
| `app/explain/root_cause.py` | `PRIMARY_METRIC_CAUSE_TEMPLATES` table per primary metric → evidence-weighted `RootCauseFinding[]`; never invents unsupported causes |
| `app/explain/confidence_score.py` | 4-component scoring: data completeness (30%), delta availability (25%), evidence strength (30%), trend consistency (15%) → 0–100% |
| `app/explain/recommendation_engine.py` | Per-metric recommendation bank with conditional triggers + priority, returns up to 5 ordered, actionable steps |
| `app/explain/prompts.py` | `EXPLAIN_ANALYST_SYSTEM_PROMPT` (no-hallucination rules) + `WHY_QUESTION_HINTS` list |
| `app/explain/explain_agent.py` | Orchestrates the pipeline, writes JSONL events to `logs/explain_events.jsonl`, supports optional LLM synthesis |
| `app/api/explain.py` | FastAPI `POST /explain` endpoint, request validation, error mapping (400 / 422 / 503 / 500) |
| `app/models/schemas.py` | `ExplainRequest`, `ExplainSummary`, `ExplainResponse` TypeScript-compatible Pydantic models |

Intent → analysis pattern:

| Metric focused on | Analysis emphasis |
|---|---|
| margin | Shipping, discounts, COGS, AOV mix, customer mix |
| revenue | Order volume, AOV, active customers, promo intensity |
| profit | Revenue, COGS, shipping, discount lines |
| shipping_cost | Order count, parcel size / AOV proxy, sales scale |
| orders | Active customers, promo conversion, revenue alignment |
| customers | Orders, retention cohorts, new-acquisition promos |
| retention | Active customer drop, AOV / LTV signals, promo dependency |

## Governance, Security & Query Transparency (Day 16)

### Architecture

```
User Question
   ↓
Security Validator  ─── SQL injection ──► block
   ↓
SQL Detector         ─── Raw SQL requests ──► block + CUBE-ONLY msg
   ↓
Expensive Query Dt.  ─── Data-dump patterns ──► block + suggested filters
   ↓
Policy Engine         (decision + JSONL log)
   ↓
LangChain Agent / Explain Engine / Semantic Router
   ↓
Cube API ONLY  →  NEVER run raw SQL / NEVER bypass Cube.dev
   ↓
AI Explanation + cube_trace payload + cube_json payload
   ↓
Frontend renders:
  ├─► View API button  (Cube API endpoint + payload + time + status + size)
  └─► View JSON button (pretty-printed Cube.dev response + Copy + Expand/Collapse)
```

Every analytics endpoint (`/ask`, `/semantic-search`, `/explain`, plus the
client-facing `/governance/validate` pre-flight check) enforces the Cube-only
policy on the server. The chat UI also runs a pre-flight `/governance/validate`
call so blocked questions never leave the browser.

### Module map

| File | Purpose |
|---|---|
| `app/governance/sql_detector.py` | 11 regex patterns (tautology, UNION SELECT, stacked queries, `SELECT *`, exfiltration, comment sequences) + 22 dangerous-DML keyword blocklist + 16 user-asks-for-SQL keyword blocklist → `SQLDetectionResult` |
| `app/governance/expensive_query_detector.py` | 30+ data-dump phrases (every order, entire database, export all) + large-count regex + 10M-row phrases + NARROWING indicators to downgrade severity |
| `app/governance/security_validator.py` | Composes the two detectors into one `SecurityDecision`. Precedence: SQL-injection → SQL-request → expensive |
| `app/governance/query_guard.py` | "Only Cube API allowed" trace recorder; redacts secrets/tokens from payloads before rendering them as transparency |
| `app/governance/policy_engine.py` | **Single public entrypoint**: `PolicyEngine.validate(question, route)` → `PolicyResult`, logs every decision via `GovernanceLogger` |
| `app/governance/governance_logger.py` | Append-only JSONL at `logs/governance_events.jsonl` — events: `policy_decision`, `cube_trace`, `error` |
| `app/governance/prompts.py` | `SECURITY_BLOCKED_MESSAGE`, `CUBE_ONLY_POLICY_MESSAGE`, `EXPENSIVE_QUERY_SUGGESTION_MESSAGE` constants |
| `app/api/governance.py` | `POST /governance/validate` endpoint consumed by the chat UI pre-flight |

### View API feature

Displayed on every assistant message when the backend returned `cube_trace`.
The modal shows:

- Cube API endpoint (`/cubejs-api/v1/load`)
- HTTP method (`POST`)
- Request payload (user question, **redacted**)
- Query parameters (route)
- Execution time (ms)
- HTTP response status + response size (bytes)

### View JSON feature

Displayed alongside View API. The viewer renders the pretty-printed Cube
response and offers **Copy to clipboard** and an **Expand / Collapse** toggle.
No tokens or secrets are included — the redaction happens server-side.

### Test coverage

Blocked: `SELECT * FROM Orders`, `DROP TABLE Customers`, `DELETE FROM Sales`,
`UNION SELECT password`, `Show entire database`, `Export all records`.
Allowed: `Monthly revenue trend`, `Sales by region`, `Revenue share by category`,
`Top customers`, `Why did profit decrease?`, `Revenue growth over time`.

## Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

The application uses these environment variables from .env:

```env
# Environment
ENVIRONMENT=development
DEBUG=True

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://metricmind:metricmind@localhost:5433/metricmind

# LLM Providers
LLM_PROVIDER=groq
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL=gpt-4o
GROQ_API_KEY="your-groq-api-key"
GROQ_MODEL=llama3-8b-8192
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_MODEL=gemini-1.5-pro

# Cube.dev
CUBE_API_URL=http://localhost:4000/cubejs-api/v1
CUBE_API_TOKEN=""
```

## Run the backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- GET / - health check root message
- GET /sales - paginated sales rows from the warehouse fact table
- GET /metrics - aggregated revenue, profit, order, and customer metrics
- POST /ask - ask a natural language business question to the BI Agent (Day 9)
- POST /semantic-search - Semantic Search & Natural Language Analytics Pipeline (Day 10)
- POST /explain - **AI Explain Results / Root Cause Analysis (Day 15)**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example requests

```bash
curl http://localhost:8000/
curl "http://localhost:8000/sales?limit=10&offset=0"
curl http://localhost:8000/metrics

# Example BI Agent request
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the total revenue last month?"}'

# Example Semantic Search request
curl -X POST http://localhost:8000/semantic-search \
  -H "Content-Type: application/json" \
  -d '{"question": "Show monthly revenue for 2025"}'

# Example Explain Results request (Day 15)
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"question": "Why did European margin decrease?"}'
```

### Example /explain response

```json
{
  "question": "Why did European margin decrease?",
  "summary": {
    "region": "Europe",
    "period": null,
    "revenue": 1420000.0,
    "cost": 1180000.0,
    "shipping_cost": 165000.0,
    "discount_amount": 78000.0,
    "profit": 240000.0,
    "margin": 16.9,
    "orders": 2840,
    "customers": 612,
    "aov": 500.0,
    "primary_metric": "margin",
    "direction_hint": "down"
  },
  "possible_reasons": [
    "Shipping costs increased by 14.0%, compressing gross margin.",
    "Discounts were higher than the prior period (change of 12.0%), reducing per-order profitability.",
    "Product / COGS costs rose by 8.0%, outpacing revenue growth."
  ],
  "confidence": 92,
  "confidence_breakdown": {
    "data_completeness_pct": 100,
    "delta_availability_pct": 100,
    "evidence_strength_pct": 90,
    "trend_consistency_pct": 95
  },
  "recommendations": [
    "Review shipping partners and negotiate rates.",
    "Reduce excessive discounts.",
    "Optimize high-cost product pricing.",
    "Improve inventory planning.",
    "Monitor regional logistics expenses weekly."
  ],
  "provider": "Groq",
  "data_source": "cube_api"
}

## Running Validation

To validate Day 9 BI Agent setup:

```bash
cd backend
python scripts/validate_day9.py
```

To validate Day 10 Semantic Search pipeline:

```bash
cd backend
python scripts/validate_day10.py
```

To validate Day 15 Explain Results Engine:

```bash
cd backend
python scripts/validate_day15.py
```

To validate Day 16 Governance, Security & Query Transparency Engine:

```bash
cd backend
python scripts/validate_day16.py
```

## Supported Questions (Day 10 Semantic Search)

- "What is the total revenue last month?"
- "Show monthly sales for 2024"
- "What was profit by product category?"
- "Show top 5 customers by total sales"
- "Show sales by region"

## Supported Questions (Day 15 Explain Results)

- "Why did European margin decrease?"
- "Why did profit fall last month?"
- "Why are shipping costs increasing?"
- "Why is revenue growing?"
- "Why did customer retention decrease?"

### Confidence Scoring (Day 15)

The returned `confidence` field (0–100%) combines four weighted components:

| Component | Weight | Meaning |
|---|---|---|
| `data_completeness_pct` | 30% | % of expected keys (rev, profit, margin, orders, cust, cost, shipping, disc, aov) present in snapshot |
| `delta_availability_pct` | 25% | % of keys with a period-over-period delta available |
| `evidence_strength_pct` | 30% | Top + avg evidence weight across root-cause findings, bonus per ≥0.5 weight finding |
| `trend_consistency_pct` | 15% | Hint (decrease/…) vs actual delta direction alignment + strong-finding ratio |

If `confidence < 70%` the response should be shown with a warning like:
*"Additional historical data may be required to confirm this analysis."*

## Troubleshooting

- If the database is unavailable, verify Docker is running and the PostgreSQL container is up.
- If the app fails to start, ensure dependencies are installed and the environment file points to the right database URL.
- If the BI Agent or Semantic Search pipeline fails, check Cube.dev is running on http://localhost:4000 and environment variables are correctly set.
- If LLM calls fail, verify API keys for your chosen provider are correctly set in .env.
- If `/explain` returns HTTP 422 (Unsupported question), rephrase as a "Why?" question: the detector looks for prefixes like `why`, `how come`, `what caused`, `explain why`, `reason for`.
- If `/explain` `confidence` is below 70%, compare a longer time window or add more specific filters (region, category, last month) to reduce uncertainty.
- Logs are written to backend/logs/ directory (backend.log, explain_events.jsonl, and day* reports).



