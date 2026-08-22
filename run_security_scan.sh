#!/bin/bash
# Scan for hardcoded secrets in Python files
echo "=== Secret Scan ==="
grep -rn --include='*.py' -E '(password|secret|api_key|token)\s*=\s*["\x27][^"\x27]{8,}' /mnt/d/Dataflow \
    --exclude-dir=tests --exclude-dir=node_modules --exclude-dir=frontend --exclude-dir=.git \
    --exclude-dir=__pycache__ --exclude='*test*' --exclude='*mock*' --exclude='*fixture*' \
    2>/dev/null | grep -vi 'getenv\|environ\|os\.get\|config\|hash\|verify\|check\|validate\|reset\|change\|prompt\|input\|placeholder\|example\|dummy\|None\|empty\|""' \
    | head -20

if [ $? -ne 0 ]; then
    echo "No hardcoded secrets found."
else
    echo ""
    echo "Potential secrets found above (review manually)."
fi

echo ""
echo "=== Docker Container Scan ==="
# Check for vulnerabilities in the built image
docker scout cves dataflow-api:latest 2>/dev/null || echo "docker scout not available, skipping container CVE scan"
