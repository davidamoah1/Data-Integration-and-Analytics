#!/bin/bash
set -e
source /opt/df_venv/bin/activate
cd /mnt/d/Dataflow

# Ensure services are running
service mysql start 2>/dev/null || true
service redis-server start 2>/dev/null || true
sleep 3

# Production environment
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
# Don't set REDIS_URL so workflow runs synchronously
# export REDIS_URL="redis://127.0.0.1:6379/0"
export API_HOST=127.0.0.1
export API_PORT=18000
export SUPER_ADMIN_EMAIL="admin@dataflow.io"
export SUPER_ADMIN_PASSWORD="AdminPass2026!"

# Kill any existing uvicorn on port 18000 — we'll use the already-running one
# pkill -f "uvicorn.*18000" 2>/dev/null || true
# sleep 1

# Verify backend is running
if ! curl -s http://127.0.0.1:18000/health > /dev/null 2>&1; then
    echo "Backend not running. Starting it..."
    pkill -f "uvicorn.*18000" 2>/dev/null || true
    sleep 1
    nohup /opt/df_venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 18000 > /tmp/backend.log 2>&1 &
    echo "Waiting for backend..."
    for i in $(seq 1 60); do
        if curl -s http://127.0.0.1:18000/health > /dev/null 2>&1; then
            echo "Backend ready after ${i}s"
            break
        fi
        sleep 1
    done
fi

echo "=== Section 4: Health & Readiness ==="
HEALTH=$(curl -s http://127.0.0.1:18000/health)
echo "Health: $HEALTH"
READY=$(curl -s http://127.0.0.1:18000/ready)
echo "Ready: $READY"
echo ""

echo "=== Section 5: Real User Signup ==="
TIMESTAMP=$(date +%s)
USER_A_EMAIL="mysql_a_${TIMESTAMP}@test.com"
USER_A_PASSWORD="TestPass123!"

SIGNUP_A=$(curl -s -X POST http://127.0.0.1:18000/api/auth/signup \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${USER_A_EMAIL}\",\"password\":\"${USER_A_PASSWORD}\",\"full_name\":\"MySQL Test User A\",\"organization_name\":\"MySQL Org A ${TIMESTAMP}\",\"country\":\"US\",\"industry\":\"retail\",\"organization_type\":\"commercial\"}")
echo "Signup A: $SIGNUP_A"

TOKEN_A=$(echo "$SIGNUP_A" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','') or d.get('data',{}).get('access_token',''))" 2>/dev/null || echo "")
if [ -z "$TOKEN_A" ]; then
    echo "ERROR: No access_token in signup response"
    exit 1
fi
echo "Token A obtained (length: ${#TOKEN_A})"
echo ""

echo "=== Section 5b: Login ==="
LOGIN_A=$(curl -s -X POST http://127.0.0.1:18000/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${USER_A_EMAIL}\",\"password\":\"${USER_A_PASSWORD}\"}")
echo "Login A: ${LOGIN_A:0:100}..."
LOGIN_TOKEN=$(echo "$LOGIN_A" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','') or d.get('data',{}).get('access_token',''))" 2>/dev/null || echo "")
if [ -z "$LOGIN_TOKEN" ]; then
    echo "ERROR: No access_token in login response"
    exit 1
fi
echo "Login token obtained (length: ${#LOGIN_TOKEN})"
echo ""

echo "=== Section 5c: Empty Workspace (no demo data) ==="
WORKSPACE_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18000/dataset-workflow/nonexistent-id/status \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Non-existent workflow status: HTTP ${WORKSPACE_CHECK} (expected 404)"
echo ""

echo "=== Section 6: Real Dataset Upload ==="
# Create a real CSV file
cat > /tmp/mysql_test_data.csv << 'CSVEOF'
date,product,region,sales,quantity,unit_price
2024-01-15,Widget A,North,1500.00,100,15.00
2024-01-16,Widget B,South,2300.00,150,15.33
2024-01-17,Widget A,East,1800.00,120,15.00
2024-01-18,Widget C,North,3200.00,80,40.00
2024-01-19,Widget B,West,2100.00,140,15.00
2024-01-20,Widget A,South,1650.00,110,15.00
2024-01-21,Widget C,East,4000.00,100,40.00
2024-01-22,Widget D,North,5500.00,50,110.00
2024-01-23,Widget B,North,2400.00,160,15.00
2024-01-24,Widget A,West,1950.00,130,15.00
CSVEOF

UPLOAD=$(curl -s -X POST "http://127.0.0.1:18000/dataset-workflow/run?admin_confirmed=true" \
    -H "Authorization: Bearer ${TOKEN_A}" \
    -F "file=@/tmp/mysql_test_data.csv")
echo "Upload: $UPLOAD"

WORKFLOW_ID=$(echo "$UPLOAD" | python -c "
import sys, json, re
d = json.load(sys.stdin)
# Try direct workflow_id
wid = d.get('workflow_id','')
if not wid:
    # Try nested data
    wid = d.get('data',{}).get('workflow_id','')
if not wid:
    # Try job_id (async path)
    wid = d.get('data',{}).get('job_id','')
if not wid:
    wid = d.get('job_id','')
if not wid:
    # Try extracting from status_url
    url = d.get('data',{}).get('status_url','') or d.get('status_url','')
    m = re.search(r'/jobs/(\d+)', url)
    if m:
        wid = m.group(1)
print(wid)
" 2>/dev/null || echo "")
if [ -z "$WORKFLOW_ID" ]; then
    echo "ERROR: No workflow_id in upload response"
    exit 1
fi
echo "Workflow/Job ID: $WORKFLOW_ID"
echo ""

echo "=== Section 6b: Wait for workflow completion ==="
for i in $(seq 1 60); do
    STATUS=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/status \
        -H "Authorization: Bearer ${TOKEN_A}")
    STATE=$(echo "$STATUS" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','') or d.get('data',{}).get('status','') or d.get('data',{}).get('current_stage',''))" 2>/dev/null || echo "")
    echo "  Status: $STATE (attempt $i)"
    if [ "$STATE" = "completed" ] || [ "$STATE" = "failed" ] || [ "$STATE" = "complete" ] || [ "$STATE" = "analysis_complete" ]; then
        break
    fi
    sleep 2
done
echo "Final status: $STATUS"
echo ""

echo "=== Section 6c: Profile ==="
PROFILE=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/profile \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Profile: ${PROFILE:0:200}..."
echo ""

echo "=== Section 6d: Quality ==="
QUALITY=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/quality \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Quality: ${QUALITY:0:200}..."
echo ""

echo "=== Section 6e: Semantic ==="
SEMANTIC=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/semantic \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Semantic: ${SEMANTIC:0:200}..."
echo ""

echo "=== Section 6f: Industry ==="
INDUSTRY=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/industry \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Industry: ${INDUSTRY:0:200}..."
echo ""

echo "=== Section 6g: Insights ==="
INSIGHTS=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/insights \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Insights: ${INSIGHTS:0:200}..."
echo ""

echo "=== Section 6h: Dashboard ==="
DASHBOARD=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/dashboard \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Dashboard: ${DASHBOARD:0:300}..."
echo ""

echo "=== Section 7: Automatic Visualization ==="
echo "$DASHBOARD" | python -c "
import sys, json
d = json.load(sys.stdin)
data = d.get('data', d)
charts = data.get('charts', data.get('visualizations', data.get('dashboard', {}).get('charts', [])))
print(f'Chart count: {len(charts)}')
for c in charts:
    ctype = c.get('chart_type', c.get('type', 'unknown'))
    title = c.get('title', c.get('name', 'untitled'))
    print(f'  - {ctype}: {title}')
kpis = data.get('kpis', data.get('dashboard', {}).get('kpis', []))
print(f'KPI count: {len(kpis)}')
for k in kpis:
    label = k.get('label', k.get('name', 'unknown'))
    value = k.get('value', 'N/A')
    print(f'  - {label}: {value}')
# Also show industry and recommendations
industry = data.get('industry', 'unknown')
print(f'Industry: {industry}')
recommended = data.get('recommended', False)
print(f'Recommended: {recommended}')
"
echo ""

echo "=== Section 9: Report Generation ==="
REPORT=$(curl -s -X POST http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/dashboard \
    -H "Authorization: Bearer ${TOKEN_A}" \
    -H "Content-Type: application/json" \
    -d '{"format":"json"}')
echo "Report: ${REPORT:0:300}..."
echo ""

echo "=== Section 10: PowerPoint Generation ==="
PPTX=$(curl -s -X POST http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/presentation \
    -H "Authorization: Bearer ${TOKEN_A}" \
    -H "Content-Type: application/json" \
    -d '{"format":"pptx"}')
echo "PPTX: ${PPTX:0:300}..."
echo ""

echo "=== Section 12: Organization Isolation ==="
USER_B_EMAIL="mysql_b_${TIMESTAMP}@test.com"
USER_B_PASSWORD="TestPass123!"

SIGNUP_B=$(curl -s -X POST http://127.0.0.1:18000/api/auth/signup \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${USER_B_EMAIL}\",\"password\":\"${USER_B_PASSWORD}\",\"full_name\":\"MySQL Test User B\",\"organization_name\":\"MySQL Org B ${TIMESTAMP}\",\"country\":\"UK\",\"industry\":\"finance\",\"organization_type\":\"commercial\"}")
echo "Signup B: ${SIGNUP_B:0:100}..."
TOKEN_B=$(echo "$SIGNUP_B" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','') or d.get('data',{}).get('access_token',''))" 2>/dev/null || echo "")

if [ -n "$TOKEN_B" ]; then
    echo "Token B obtained"
    ISOLATION=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/status \
        -H "Authorization: Bearer ${TOKEN_B}")
    echo "Org B accessing Org A workflow: HTTP ${ISOLATION} (expected 403)"
else
    echo "ERROR: No token for User B"
fi
echo ""

echo "=== Section 11: Authentication Tests ==="
NO_AUTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/status)
echo "No auth: HTTP ${NO_AUTH} (expected 401)"

BAD_AUTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/status \
    -H "Authorization: Bearer invalidtoken123")
echo "Bad auth: HTTP ${BAD_AUTH} (expected 401)"
echo ""

echo "=== Section 14: Redis Check ==="
redis-cli ping
echo ""

echo "=== Section 15: Backup Test ==="
BACKUP_RESULT=$(/opt/df_venv/bin/python -c "
import sys
sys.path.insert(0, '/mnt/d/Dataflow')
import os
os.environ['APP_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'mysql+pymysql://dataflow:DataflowProd2026!@127.0.0.1:3306/dataflow_prod?charset=utf8mb4'
os.environ['JWT_SECRET_KEY'] = 'production-validation-secret-key-32chars-min'
os.environ['ENCRYPTION_KEY'] = 'dGVzdC1lbmNyeXB0aW9uLWtleS1mb3ItdmFsaWRhdGlvbjEyMzQ='
os.environ['CORS_ORIGINS'] = 'https://app.example.com'
os.environ['STORAGE_BACKEND'] = 'local'
os.environ['ALLOW_LOCAL_STORAGE_IN_PRODUCTION'] = '1'
os.environ['SEED_DEMO_DATA'] = 'false'
os.environ['DISABLE_CONFIG_VALIDATION'] = '1'

from database.backup import BackupManager
bm = BackupManager()
result = bm.create_backup()
print(f'Backup created: {result}')
" 2>&1)
echo "Backup: $BACKUP_RESULT"
echo ""

echo "=== Section 12b: Persistence Test - Restart Backend ==="
echo "Killing backend..."
pkill -f "uvicorn.*18000" 2>/dev/null || true
sleep 5

echo "Restarting backend..."
nohup /opt/df_venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 18000 > /tmp/backend2.log 2>&1 &

for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:18000/health > /dev/null 2>&1; then
        echo "Backend restarted after ${i}s"
        break
    fi
    sleep 1
done

echo "Verifying data persisted after restart..."
PERSIST_STATUS=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/status \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Persisted workflow status: ${PERSIST_STATUS:0:200}..."

PERSIST_PROFILE=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WORKFLOW_ID}/profile \
    -H "Authorization: Bearer ${TOKEN_A}")
echo "Persisted profile: ${PERSIST_PROFILE:0:200}..."
echo ""

echo "=== Cleanup ==="
# Leave backend running for additional tests

echo ""
echo "=== ALL E2E TESTS DONE ==="
