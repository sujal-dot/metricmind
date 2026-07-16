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
│   │   └── generate_report.py    # Generate cleaning report
│   ├── sql/
│   │   └── schema.sql            # Database schema
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

