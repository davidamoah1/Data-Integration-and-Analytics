# Runbooks

## RB-001: Restart Backend Service

**Symptom**: Backend unresponsive, 502 errors from Nginx

```bash
sudo systemctl restart dataflow
sleep 5
curl http://localhost:8080/health
```

If health check fails:
```bash
journalctl -u dataflow --since "5 min ago" --no-pager
```

---

## RB-002: Database Connection Issues

**Symptom**: "Database connection failed" errors in logs

```bash
# Check MySQL status
sudo systemctl status mysql

# Check connections
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

# Restart MySQL if needed
sudo systemctl restart mysql

# Verify
mysql -u root -p -e "SELECT 1;"
```

---

## RB-003: High CPU Usage

**Symptom**: CPU > 90%, slow API responses

```bash
# Identify process
top -bn1 | head -20

# Check API workers
ps aux | grep gunicorn

# Reduce workers if needed
# Edit /etc/systemd/system/dataflow.service
# Restart
sudo systemctl daemon-reload
sudo systemctl restart dataflow
```

---

## RB-004: Disk Space Full

**Symptom**: "No space left on device" errors

```bash
# Check disk
df -h

# Find large files
du -sh /var/log/* | sort -rh | head -10

# Clean old logs
journalctl --vacuum-time=7d

# Clean old backups
find /backups -name "*.sql.gz" -mtime +30 -delete

# Clean temp files
rm -rf /tmp/dataflow_*
```

---

## RB-005: Suspend a Tenant

**Symptom**: Customer requested suspension or non-payment

```bash
# Via API
curl -X POST https://api.yourdomain.com/admin-portal/tenants/{org_id}/suspend \
  -H "Authorization: Bearer <admin-token>"

# Verify
curl https://api.yourdomain.com/admin-portal/tenants/{org_id} \
  -H "Authorization: Bearer <admin-token>"
```

---

## RB-006: Deploy New Version

```bash
# 1. Backup database
mysqldump -u root -p dataflow > /backups/pre_deploy_$(date +%Y%m%d).sql

# 2. Pull latest code
cd /app && git pull origin main

# 3. Install dependencies
pip install -r requirements.txt

# 4. Restart service
sudo systemctl restart dataflow

# 5. Verify health
curl http://localhost:8080/health

# 6. Run smoke tests
python -m pytest tests/test_smoke.py -v
```

---

## RB-007: Rollback Deployment

```bash
# 1. Stop service
sudo systemctl stop dataflow

# 2. Revert code
git log --oneline -5
git checkout <previous-commit>

# 3. Restore database if needed
mysql -u root -p dataflow < /backups/pre_deploy_YYYYMMDD.sql

# 4. Restart
sudo systemctl start dataflow

# 5. Verify
curl http://localhost:8080/health
```

---

## RB-008: Create System Announcement

```bash
curl -X POST https://api.yourdomain.com/saas/announcements \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Scheduled Maintenance",
    "message": "The platform will be unavailable on Saturday 2-4 AM UTC for maintenance.",
    "severity": "warning",
    "target_audience": "all",
    "ends_at": "2026-08-01T04:00:00Z"
  }'
```

---

## RB-009: Check Tenant Health Score

```bash
curl https://api.yourdomain.com/saas/health-score \
  -H "Authorization: Bearer <token>"
```

Scores:
- 70-100: Healthy
- 40-69: At Risk
- 0-39: Critical

---

## RB-010: Enable Feature for Organization

```bash
curl -X POST https://api.yourdomain.com/saas/features/override \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "flag_key": "automl",
    "is_enabled": true,
    "reason": "beta_access"
  }'
```
