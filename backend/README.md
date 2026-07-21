# MetricMind Backend

## Overview

This backend exposes a FastAPI service for the MetricMind analytics platform. It connects to the existing PostgreSQL warehouse and exposes REST endpoints for sales and aggregated metrics.

## Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment

The application reads database settings from .env.

## Run the backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- GET / - health check root message
- GET /sales - paginated sales rows from the warehouse fact table
- GET /metrics - aggregated revenue, profit, order, and customer metrics
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example requests

```bash
curl http://localhost:8000/
curl "http://localhost:8000/sales?limit=10&offset=0"
curl http://localhost:8000/metrics
```

## Troubleshooting

- If the database is unavailable, verify Docker is running and the PostgreSQL container is up.
- If the app fails to start, ensure dependencies are installed and the environment file points to the right database URL.
- Logs are written to backend/logs/backend.log.


