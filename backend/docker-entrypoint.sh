#!/bin/sh
set -e

echo "=== MetricMind Backend Entrypoint ==="

# Step 1: Wait for Postgres (timeout 60s)
echo "Step 1/4: Waiting for PostgreSQL to be ready..."
DB_HOST=$(python -c "import os; from urllib.parse import urlparse; u=urlparse(os.environ.get('DATABASE_URL','')); print(u.hostname or 'postgres')")
DB_PORT=$(python -c "import os; from urllib.parse import urlparse; u=urlparse(os.environ.get('DATABASE_URL','')); print(u.port or 5432)")
DB_USER=$(python -c "import os; from urllib.parse import urlparse; u=urlparse(os.environ.get('DATABASE_URL','')); print(u.username or 'metricmind')")

timeout 60s sh -c "
until pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} > /dev/null 2>&1; do
    echo 'Postgres is unavailable - sleeping...'
    sleep 2
done
"
echo "PostgreSQL is ready."

# Step 2: Run Alembic migrations
if [ "${RUN_MIGRATIONS_ON_STARTUP:-0}" = "1" ]; then
    echo "Step 2/4: Running Alembic database migrations..."
    cd /app && python -m alembic upgrade head
    echo "Migrations completed successfully."
else
    echo "Step 2/4: RUN_MIGRATIONS_ON_STARTUP not set to 1, skipping migrations."
fi

# Step 3: Run seed script if SEED_ON_BOOT=1
if [ "${SEED_ON_BOOT:-0}" = "1" ]; then
    echo "Step 3/4: SEED_ON_BOOT=1 detected, running seed script..."
    if [ -f /app/scripts/seed_data.py ]; then
        cd /app && python scripts/seed_data.py
        echo "Seed script completed successfully."
    else
        echo "Warning: SEED_ON_BOOT=1 but scripts/seed_data.py not found, skipping seed."
    fi
else
    echo "Step 3/4: SEED_ON_BOOT not set, skipping seed."
fi

# Step 4: Start Uvicorn
echo "Step 4/4: Starting Uvicorn server with ${UVICORN_WORKERS:-2} workers..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}
