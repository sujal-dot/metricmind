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
│   │   ├── import_csv.py       # CSV import pipeline
│   │   └── validate_data.py    # Data validation script
│   ├── sql/
│   │   └── schema.sql          # Database schema
│   ├── logs/                   # Import/validation logs
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

