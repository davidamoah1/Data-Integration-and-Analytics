#!/bin/bash
source /opt/df_venv/bin/activate
cd /mnt/d/Dataflow

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

TS=$(date +%s)
EMAIL="debug_${TS}@test.com"
PASS="TestPass123!"

echo "=== Signup ==="
RESP=$(curl -s -X POST http://127.0.0.1:18000/api/auth/signup \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\",\"full_name\":\"Debug User\",\"organization_name\":\"Debug Org ${TS}\",\"country\":\"US\",\"industry\":\"retail\",\"organization_type\":\"commercial\"}")
echo "$RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:500])"

TOKEN=$(echo "$RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','') or d.get('data',{}).get('access_token',''))")
echo "Token: ${TOKEN:0:50}..."

echo ""
echo "=== Upload CSV ==="
cat > /tmp/debug_data.csv << 'CSVEOF'
date,product,region,sales,quantity
2024-01-15,Widget A,North,1500.00,100
2024-01-16,Widget B,South,2300.00,150
2024-01-17,Widget A,East,1800.00,120
2024-01-18,Widget C,North,3200.00,80
2024-01-19,Widget B,West,2100.00,140
CSVEOF

UPLOAD=$(curl -s -X POST http://127.0.0.1:18000/dataset-workflow/run \
    -H "Authorization: Bearer ${TOKEN}" \
    -F "file=@/tmp/debug_data.csv")
echo "Upload response:"
echo "$UPLOAD" | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:1000])"

WID=$(echo "$UPLOAD" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('workflow_id','') or d.get('workflow_id',''))")
echo "Workflow ID: $WID"

echo ""
echo "=== Status ==="
STATUS=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WID}/status \
    -H "Authorization: Bearer ${TOKEN}")
echo "Status response:"
echo "$STATUS" | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:1000])"

echo ""
echo "=== Profile ==="
PROFILE=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WID}/profile \
    -H "Authorization: Bearer ${TOKEN}")
echo "Profile response:"
echo "$PROFILE" | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:1000])"

echo ""
echo "=== Dashboard ==="
DASH=$(curl -s http://127.0.0.1:18000/dataset-workflow/${WID}/dashboard \
    -H "Authorization: Bearer ${TOKEN}")
echo "Dashboard response:"
echo "$DASH" | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d, indent=2)[:1500])"

echo ""
echo "=== DONE ==="
