# MetricMind Backend

## Overview

This backend exposes a FastAPI service for the MetricMind analytics platform. It connects to the existing PostgreSQL warehouse and exposes REST endpoints for sales, aggregated metrics, and a LangChain BI Agent that answers natural language business questions via Cube.dev.

## LangChain BI Agent Architecture

- **BI Agent**: A LangChain agent that uses an LLM to understand natural language questions and uses Cube.dev to retrieve analytics
- **LLM Factory**: Supports Groq, OpenAI, and Gemini LLMs
- **Cube Client**: Connects to the agent to Cube.dev
- **Tools**: Custom LangChain tools for querying Cube.dev
- **Endpoints**: New `/ask` endpoint for BI queries

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
- POST /ask - ask a natural language business question to the BI Agent
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
```

## Running the BI Agent Validation

To validate the BI Agent setup, run:

```bash
cd backend
python scripts/validate_day9.py
```

## Troubleshooting

- If the database is unavailable, verify Docker is running and the PostgreSQL container is up.
- If the app fails to start, ensure dependencies are installed and the environment file points to the right database URL.
- If the BI Agent fails, check Cube.dev is running on http://localhost:4000 and environment variables are correctly set.
- Logs are written to backend/logs/ directory.



