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
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
├── cube/
├── dbt/
├── docs/
├── data/
├── docker-compose.yml
├── .gitignore
└── README.md
```

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

