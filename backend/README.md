# MetricMind Backend

## Setup

1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (especially DATABASE_URL)
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Data Warehouse

### Import Data
Place CSV files in `../data/raw/`, then run:
```bash
python scripts/import_csv.py
```

### Validate Data
After import, validate:
```bash
python scripts/validate_data.py
```

### Logs
Logs are stored in `logs/` directory


