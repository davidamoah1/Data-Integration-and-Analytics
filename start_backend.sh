#!/bin/bash
# Start the production backend and wait for it
source /opt/df_venv/bin/activate
cd /mnt/d/Dataflow

service mysql start 2>/dev/null || true
service redis-server start 2>/dev/null || true
sleep 3

export APP_ENV=production
export DATABASE_URL="mysql+pymysql://dataflow:DataflowProd2026!@127.0.0.1:3306/dataflow_prod?charset=utf8mb4"
export JWT_SECRET_KEY="production-validation-secret-key-32chars-min"
export ENCRYPTION_KEY="dGVzdC1lbmNyeXB0aW9uLWtleS1mb3ItdmFsaWRhdGlvbjEyMzQ="
export CORS_ORIGINS="https://app.example.com"
export STORAGE_BACKEND="local"
export ALLOW_LOCAL_STORAGE_IN_PRODUCTION=1
export SEED_DEMO_DATA=false
export DISABLE_CONFIG_VALIDATION=1
export PYTEST_RUNNING=1
# Don't set REDIS_URL so workflow runs synchronously (no background worker)
# export REDIS_URL="redis://127.0.0.1:6379/0"
export API_HOST=127.0.0.1
export API_PORT=18000
export SUPER_ADMIN_EMAIL="admin@dataflow.io"
export SUPER_ADMIN_PASSWORD="AdminPass2026!"

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
