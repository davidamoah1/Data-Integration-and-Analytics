#!/bin/bash
# Start the production backend locally for validation.
# All secrets must come from environment variables or .env — never hardcoded.
source /opt/df_venv/bin/activate 2>/dev/null || true
cd /mnt/d/Dataflow

service mysql start 2>/dev/null || true
service redis-server start 2>/dev/null || true
sleep 3

# Require environment variables to be set externally (e.g. via .env)
export APP_ENV="${APP_ENV:-production}"
export DB_TYPE="${DB_TYPE:-mysql}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export STORAGE_BACKEND="${STORAGE_BACKEND:-local}"
export ALLOW_LOCAL_STORAGE_IN_PRODUCTION="${ALLOW_LOCAL_STORAGE_IN_PRODUCTION:-1}"
export SEED_DEMO_DATA="${SEED_DEMO_DATA:-false}"
export DISABLE_CONFIG_VALIDATION="${DISABLE_CONFIG_VALIDATION:-1}"
export PYTEST_RUNNING="${PYTEST_RUNNING:-1}"
export API_HOST="${API_HOST:-127.0.0.1}"
export API_PORT="${API_PORT:-18000}"

# Verify required secrets are set
if [ -z "$DATABASE_URL" ] && [ -z "$MYSQL_HOST" ]; then
    echo "ERROR: DATABASE_URL or MYSQL_HOST must be set in environment."
    exit 1
fi
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "ERROR: JWT_SECRET_KEY must be set in environment."
    exit 1
fi

pkill -f "uvicorn.*18000" 2>/dev/null || true
sleep 2

nohup /opt/df_venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 18000 > /tmp/backend.log 2>&1 &
echo "Backend PID: $!"

echo "Waiting up to 60s for backend..."
for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:18000/health > /dev/null 2>&1; then
        echo "Backend ready after ${i}s"
        curl -s http://127.0.0.1:18000/health
        echo ""
        curl -s http://127.0.0.1:18000/ready
        echo ""
        exit 0
    fi
    sleep 1
done

echo "Backend failed to start. Last 30 lines of log:"
tail -30 /tmp/backend.log
exit 1
