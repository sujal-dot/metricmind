# MetricMind – Agentic Business Intelligence

A professional, scalable, enterprise-grade AI-powered Business Intelligence platform.

## Tech Stack

### Backend
- Python 3.12+
- FastAPI
- Uvicorn
- LangChain
- OpenAI API
- Groq API
- Pandas
- NumPy
- SQLAlchemy
- PostgreSQL
- Psycopg2
- Pydantic
- python-dotenv

### Frontend
- Next.js (Latest)
- TypeScript
- Tailwind CSS
- App Router
- ESLint
- Tremor
- Apache ECharts
- Axios
- React Hook Form
- Zod
- TanStack Query
- Lucide React

### Database
- PostgreSQL

### Containerization
- Docker
- Docker Compose

## Project Structure

```
metricmind/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── config/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── scripts/
│   │   ├── import_csv.py         # CSV import pipeline
│   │   ├── validate_data.py      # Data validation script
│   │   ├── clean_data.py         # Data cleaning pipeline
│   │   ├── validate_clean_data.py # Validate cleaned data
│   │   ├── generate_report.py    # Generate cleaning report
│   │   ├── build_star_schema.py  # Build star schema for BI
│   │   └── validate_star_schema.py # Validate star schema
│   ├── sql/
│   │   ├── schema.sql            # Database schema (normalized)
│   │   └── star_schema/          # Star schema SQL DDL files
│   ├── logs/                     # Import/validation/cleaning logs
│   ├── reports/                  # Cleaning and other reports
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
├── cube/
├── dbt/
├── docs/
├── data/
│   ├── raw/                    # Raw CSV files
│   └── processed/              # Processed data (if needed)
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Day 2: Data Warehouse Setup

### Dataset
This project uses the **Superstore Sales Dataset** (a standard sample dataset for business intelligence). The dataset is provided as `all.csv` in `data/raw/`.

### Import Instructions
1. Ensure PostgreSQL is running:
   ```bash
   docker-compose up -d
   ```
2. Activate backend venv and install dependencies (if not done already):
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the import pipeline:
   ```bash
   python scripts/import_csv.py
   ```

### Validation Instructions
After importing, validate the data:
```bash
python scripts/validate_data.py
```

### Database Schema
The database is normalized into the following tables:
- `regions`: Sales regions (South, West, Central, East)
- `states`: US states/provinces
- `cities`: Cities with postal codes
- `segments`: Customer segments (Consumer, Corporate, Home Office)
- `categories`: Product categories (Furniture, Office Supplies, Technology)
- `subcategories`: Product subcategories
- `products`: Product details
- `ship_modes`: Shipping modes
- `customers`: Customer information
- `orders`: Order headers
- `order_details`: Order line items (sales, quantity, discount, profit)
- `import_logs`: Tracks import history

### Rerunning Imports Safely
The import script tracks imported files in the `import_logs` table and skips already imported files. To re‑import:
- Delete the relevant entries from `import_logs`, or
- Remove and re‑add the CSV file, or
- Truncate tables first (use caution!)

### Troubleshooting
- **Connection errors**: Verify `DATABASE_URL` in `backend/.env` is correct
- **Missing CSV files**: Ensure `all.csv` is in `data/raw/`
- **Import logs**: Check `backend/logs/` for detailed import/validation logs


## Day 3: Data Cleaning Pipeline

### Overview
The data cleaning pipeline processes raw sales data and produces a clean, standardized dataset for analysis.

### Cleaning Steps Performed
1. **Remove Duplicates**: Remove duplicate records, preserve first valid row
2. **Handle Missing Values**: Text → "Unknown", numeric → median, critical missing values → remove row
3. **Standardize Column Names**: Convert to snake_case, lowercase
4. **Fix Dates**: Convert all dates to `YYYY-MM-DD`
5. **Standardize Text**: Trim whitespace, normalize encoding
6. **Validate Numerics**: Ensure sales, profit, quantity, discount are valid numbers
7. **Data Types**: Correct type mismatches
8. **Remove Invalid Records**: Remove unrecoverable rows
9. **Final Validation**: Verify all checks

### How to Run the Pipeline
1. Ensure raw data exists in `data/raw/` (e.g., `all.csv`)
2. Run the cleaning script:
   ```bash
   cd backend
   python scripts/clean_data.py
   ```
3. Validate the cleaned data:
   ```bash
   python scripts/validate_clean_data.py
   ```
4. Generate cleaning report:
   ```bash
   python scripts/generate_report.py
   ```

### Output Locations
- **Cleaned Data**: `data/processed/clean_sales.csv`
- **Cleaning Logs**: `backend/logs/`
- **Cleaning Report**: `backend/reports/cleaning_report.md`
- **Metrics**: `backend/reports/cleaning_metrics.json`


## Day 4: Star Schema for BI & OLAP

### Overview
Build a Kimball-style star schema optimized for BI and OLAP queries using the cleaned sales dataset.

### Star Schema Design
#### Fact Table
- **`fact_sales`**:
  - `sales_key` (PK, surrogate key): Unique identifier for each fact
  - `order_id`: Order ID from source system
  - `customer_key` (FK): References `dim_customer.customer_key`
  - `product_key` (FK): References `dim_product.product_key`
  - `date_key` (FK): References `dim_date.date_key`
  - `region_key` (FK): References `dim_region.region_key`
  - `employee_key` (FK, nullable): References `dim_employee.employee_key`
  - `sales_amount`: Total sales amount
  - `quantity`: Number of units sold
  - `discount`: Discount applied
  - `profit_amount`: Profit from sale

#### Dimension Tables
- **`dim_customer`**:
  - `customer_key` (PK): Surrogate key
  - `customer_id`: Customer ID
  - `customer_name`: Customer's name
  - `segment`: Customer segment
  - `created_at`: Timestamp when record was inserted

- **`dim_product`**:
  - `product_key` (PK): Surrogate key
  - `product_id`: Product ID
  - `product_name`: Product name
  - `category`: Product category
  - `sub_category`: Product subcategory
  - `created_at`: Timestamp when record was inserted

- **`dim_date`**:
  - `date_key` (PK): Integer key (YYYYMMDD)
  - `full_date`: Full date
  - `day_of_month`: Day of month
  - `month`: Month number
  - `month_name`: Month name
  - `year`: Year
  - `quarter`: Quarter
  - `day_of_week`: Day of week
  - `week_number`: ISO week number
  - `is_weekend`: Boolean indicating weekend

- **`dim_region`**:
  - `region_key` (PK): Surrogate key
  - `country`: Country
  - `state`: State/province
  - `city`: City
  - `region`: Sales region
  - `created_at`: Timestamp when record was inserted

- **`dim_employee`** (for future use):
  - `employee_key` (PK): Surrogate key
  - `employee_id`: Employee ID
  - `employee_name`: Employee name
  - `department`: Department
  - `created_at`: Timestamp when record was inserted


### How to Build the Star Schema
1. Ensure PostgreSQL is running and cleaned data is available in `data/processed/clean_sales.csv`
2. Run the build script:
   ```bash
   cd backend
   python scripts/build_star_schema.py
   ```
3. Validate the star schema:
   ```bash
   python scripts/validate_star_schema.py
   ```

### Schema Files
All SQL DDL files for creating tables are located at `backend/sql/star_schema/`.


## Day 16: Governance, Security & Query Transparency

### Overview

The Day 16 Governance Layer protects the MetricMind platform from unsafe queries while
providing **full transparency** into how the AI generated every answer. Every analytics
request is validated **before** it reaches the AI agent, and all analytics are served
**exclusively through the Cube.dev Semantic API** — no direct SQL, no raw database
drivers, ever.

### End-to-End Workflow

```text
User Question
      ↓
Security Validator  ← (SQL injection / raw SQL / expensive checks)
      ↓
Governance Policy Engine
      ↓
Intent Detection
      ↓
LangChain Agent
      ↓
Cube API  ← ONLY Cube.dev — never direct SQL
      ↓
JSON Response
      ↓
AI Explanation + Visualization
      ↓
View API / View JSON  ← full query transparency in the UI
```

### Project Structure Additions (Day 16)

```
metricmind/
├── backend/
│   ├── app/
│   │   ├── governance/
│   │   │   ├── __init__.py
│   │   │   ├── security_validator.py      # Composes SQL + expensive checks
│   │   │   ├── query_guard.py             # Only Cube API Allowed + trace recording
│   │   │   ├── sql_detector.py            # SQL injection + raw-SQL heuristics
│   │   │   ├── expensive_query_detector.py# Data-dump / large-row detection
│   │   │   ├── policy_engine.py           # Unified entry: validate + log + trace
│   │   │   ├── governance_logger.py       # JSONL to backend/logs/governance_events.jsonl
│   │   │   └── prompts.py                 # Standard policy messages
│   │   ├── api/
│   │   │   └── governance.py              # POST /governance/validate (pre-flight)
│   │   └── main.py                        # /ask, /semantic-search, /explain all re-validate
│   ├── logs/
│   │   └── governance_events.jsonl        # Structured audit log (auto-created)
│   └── scripts/
│       └── validate_day16.py              # PASS / FAIL report for Day 16
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── governance/
│       │   │   ├── ViewAPIButton.tsx      # Shows Cube endpoint + payload + timing
│       │   │   ├── ViewJSONButton.tsx     # Shows raw Cube JSON + copy + collapse
│       │   │   ├── APIModal.tsx           # Modal for the View API button
│       │   │   ├── JSONViewer.tsx         # Modal with pretty-printed JSON viewer
│       │   │   ├── SecurityBanner.tsx     # "Cube.dev Only" banner in chat
│       │   │   ├── PolicyViolation.tsx    # Red/orange violation panel when blocked
│       │   │   └── index.ts               # Barrel export
│       │   ├── ChatMessage.tsx            # Renders View API / View JSON buttons
│       │   └── ChatWindow.tsx             # Renders SecurityBanner on top
│       ├── hooks/
│       │   └── useChat.ts                 # Pre-flight POST /governance/validate call
│       ├── lib/
│       │   └── api.ts                     # api.governanceValidate client method
│       └── types/
│           ├── api.ts                     # CubeTrace, SecurityDecision, GovernanceResponse
│           └── chat.ts                    # cube_trace, cube_json, policy_violation on ChatMessage
```

### Security Rules

#### ❌ SQL Injection Prevention

The `SQLDetector` (`sql_detector.py`) scans the user question for dangerous
patterns and blocks them **before** any LLM call. Blocked patterns include:

- Injection tautologies: `OR 1=1`, `' OR 'a'='a'`
- SQL comments: `--`, `/* ... */`
- Stacked / second statements: `; DROP`, `; DELETE`
- DML / DDL keywords: `DROP TABLE`, `DELETE FROM`, `INSERT INTO`, `UPDATE`,
  `ALTER TABLE`, `CREATE TABLE`, `TRUNCATE`, `EXEC`, `EXECUTE`
- System tables / procs: `xp_cmdshell`, `INFORMATION_SCHEMA`, `pg_catalog`,
  `sqlite_master`, `sysobjects`
- Raw exfiltration: `INTO OUTFILE`, `COPY ... TO`
- `SELECT * FROM`

When blocked, the user sees:
> "This request violates the security policy and has been blocked."

#### ❌ Raw SQL Generation Prevention

If the user explicitly asks for SQL (`write sql`, `generate sql`, `run sql`,
`raw sql`, `sql statement`, etc.) or pastes a `SELECT … FROM …` snippet, the
governance layer blocks the request and returns:

> "MetricMind only supports analytics through the Cube.dev Semantic API. Direct
> SQL access is disabled by governance policy."

The backend **never** generates, returns, executes, or explains SQL — all
analytics go through the Cube.dev semantic layer.

#### ❌ Expensive / Over-Broad Queries

`ExpensiveQueryDetector` flags data-dump and over-broad requests such as:
- "every order ever made", "all transactions ever", "entire database / table"
- "export all records", "export everything", "dump the database"
- "show 10 million rows", "millions of records"

If one of these patterns is present and the question has **no narrowing
indicators** (time, region, category, `top N`, monthly/yearly aggregations),
the request is rejected and the user is shown:

> "This request may return too much data and was blocked for performance
> reasons. Please add filters such as a date range (e.g. 'last month'),
> region, category, or product to narrow the scope."

Up to three concrete filters are suggested (time, region, category/ranking).

### Cube API-Only Policy

The `QueryGuard` (`query_guard.py`) enforces the "Only Cube API" rule:

- Questions that pass SecurityValidator proceed; rejected questions never
  reach the agent.
- Downstream code must hand a **pre-fetched Cube JSON payload** to
  `attach_cube_trace()`; the governance classes do not import or call any
  raw DB drivers themselves.
- `CubeAPITrace` records endpoint, method, request payload, query parameters,
  execution time, status, and response size — and automatically **redacts
  any key whose name contains `token`, `secret`, `key`, `auth`, `password`,
  or `cookie`** so the frontend never sees credentials.

Every BI endpoint (`/ask`, `/semantic-search`, `/explain`) already runs
`PolicyEngine.validate(question)` first and then attaches transparency data,
so bypassing the frontend pre-flight check still results in a server-side
block.

### Query Transparency (Frontend UI)

Every successful assistant message now shows two small, unobtrusive buttons:

- **View API** — opens `APIModal` and displays:
  - Cube API endpoint and HTTP method
  - Request payload and query parameters (redacted)
  - Execution time, response status (color-coded green/red), and response size
- **View JSON** — opens `JSONViewer` and displays:
  - Pretty-printed raw Cube API JSON
  - **Copy to clipboard** (shows "Copied!" for 2s)
  - Expand / Collapse toggle for large responses

The chat header also shows a green **SecurityBanner** stating
"Cube.dev Only — No Direct SQL, Ever" and explains the governance flow.

### Policy Violations in the UI

If the governance layer blocks a question, `ChatMessage` renders the
`PolicyViolation` component instead of the regular answer:

- Red / amber / orange tone based on block code (`sql_injection`,
  `sql_request`, `expensive`)
- The exact human-readable policy message
- The matched reasons ("why it was blocked")
- Suggested filters for expensive queries
- Optional dismiss button

This same panel is shown both in the frontend pre-flight path and in the
backend server-side rejection (converted from the 403 HTTP error).

### Governance API — Pre-flight Endpoint

**`POST /governance/validate`**

Used by the frontend before sending a question to `/ask`. Runs the full
PolicyEngine without executing the question.

Request body:
```json
{
  "question": "SELECT * FROM Orders",
  "route": "/ask"
}
```

Response:
```json
{
  "question": "SELECT * FROM Orders",
  "decision": {
    "allowed": false,
    "block_reason": "This request violates the security policy and has been blocked.",
    "block_code": "sql_injection",
    "suggested_filters": [],
    "has_sql_injection": true,
    "has_sql_request": false,
    "is_expensive": false,
    "matched_reasons": ["select_star"]
  },
  "cube_trace": null,
  "cube_json": null
}
```

### Logging & Audit Trail

`GovernanceLogger` writes append-only JSONL records to
`backend/logs/governance_events.jsonl`. Event types:

- `policy_decision` — every `validate()` call, including:
  question, route, allowed flag, block_code, block_reason, matched reasons,
  suggested filters, and validation duration.
- `cube_trace` — written for successful Cube requests: question, route,
  endpoint, execution time, status, response size (no full JSON body —
  keeps log size reasonable).
- `error` — ValueError / RuntimeError / unhandled exceptions in BI /
  semantic / explain endpoints.

To audit:
```bash
tail -n 100 backend/logs/governance_events.jsonl | jq -s .
```

### Validation (Pass / Fail Report)

Run the comprehensive Day 16 test suite:
```bash
cd backend
python scripts/validate_day16.py
```

It validates:

| Category              | What it checks                                                              |
| --------------------- | --------------------------------------------------------------------------- |
| SQL Injection         | `SELECT *`, `DROP TABLE`, `UNION SELECT`, `OR 1=1`, `xp_cmdshell`, etc.     |
| Raw SQL Prevention    | `write sql`, `generate sql`, `run sql`, `select … from` snippets            |
| Expensive Guard       | "entire database", "export all records", "10 million rows"                  |
| Allowed Queries       | Monthly trend, Sales by region, Top customers, Why-did-profit-drop, etc.   |
| Policy Engine         | `PolicyEngine` composition + logger + cube-only message                     |
| QueryGuard / Trace    | `CubeAPITrace.for_view_api()` / `.for_view_json()` + redaction              |
| Transparency UI       | `ViewAPIButton.tsx`, `ViewJSONButton.tsx`, `JSONViewer.tsx` exist           |
| README Updated        | Governance / security / Cube-only / transparency docs are present           |

The script prints the PASS / FAIL report, writes a summary to
`backend/logs/day16-final-report.txt`, and exits non-zero on any failure.

### Troubleshooting

#### A valid question is being blocked as "expensive"
Add narrowing indicators such as:
- **Time**: "last month", "Q1 2025", "weekly"
- **Region**: "for Europe", "in North America"
- **Product**: "by category", "Technology products"
- **Ranking**: "top 10 customers", "top 5 products"

The `NARROWING_INDICATORS` list in `expensive_query_detector.py` contains all
recognized narrowing tokens and phrases.

#### I get a 403 from `/ask` / `/semantic-search` / `/explain`
The question is being blocked server-side by `PolicyEngine`. Use the
pre-flight endpoint first to get the human-readable reason and matched
reasons / suggested filters:
```bash
curl -X POST http://localhost:8000/governance/validate \
  -H 'Content-Type: application/json' \
  -d '{"question":"<your question>","route":"/ask"}' | jq
```

#### The "View API" / "View JSON" buttons are disabled
`cube_trace` / `cube_json` are absent. Confirm:
- Backend version ≥ Day 16 (transparency attachments in `main.py`,
  `api/semantic.py`, `api/explain.py`)
- Cube service is reachable (an error response means empty Cube JSON).

#### Governance logs are not written
`GovernanceLogger` creates `backend/logs/` automatically. Ensure the backend
process has write permissions to that directory. The path is resolved
relative to the backend package, so it works when running from the repo
root via `uvicorn app.main:app` as well as from `backend/`.


## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose

### Setup

1. **Start PostgreSQL with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## License
MIT

