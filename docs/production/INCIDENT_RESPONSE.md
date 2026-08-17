# Incident Response Procedures

**Version:** 1.0.0
**Last Updated:** 2025-01-17

---

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|-----------|---------------|----------|
| P1 - Critical | Service completely down | 15 minutes | Database unreachable, app won't start |
| P2 - High | Major feature broken | 1 hour | Workflow fails, auth broken |
| P3 - Medium | Feature degraded | 4 hours | Slow queries, partial failures |
| P4 - Low | Minor issue | Next business day | UI glitch, non-critical warning |

## Immediate Response Steps

### 1. Assess Severity

```bash
# Check application health
curl https://app.yourdomain.com/health
curl https://app.yourdomain.com/ready

# Check service status
docker-compose ps
# or
systemctl status dataflow-api
```

### 2. Determine Impact

- How many users affected?
- Which features are broken?
- Is data at risk?
- Is there data loss?

### 3. Communicate

- Notify team via agreed channel
- Post status update if public-facing

---

## Common Incidents

### Application Won't Start

```bash
# Check logs
docker logs dataflow-api --tail 100
# or
journalctl -u dataflow-api --since "5 min ago"

# Common causes:
# - Database unreachable → check MySQL status
# - Missing env variables → check .env
# - Port already in use → kill conflicting process
# - Migration not applied → alembic upgrade head
```

### Database Connection Failures

```bash
# Check MySQL is running
mysqladmin -u root ping

# Check connections
mysql -u root -e "SHOW STATUS LIKE 'Threads_connected';"
mysql -u root -e "SHOW PROCESSLIST;"

# If pool exhaustion:
# Restart the application (clears pool)
# Then investigate connection leaks
```

### High Error Rate

```bash
# Check recent errors in logs
grep "ERROR" /var/log/dataflow/app.log | tail -50

# Check if specific endpoint is failing
# Review Sentry/monitoring dashboard

# If a specific endpoint:
# 1. Check if it's a code bug (recent deployment?)
# 2. Check if it's data-related (specific user/org?)
# 3. Consider rollback if recent deployment caused it
```

### Slow Response Times

```bash
# Check slow query log
grep "Slow query" /var/log/dataflow/app.log | tail -20

# Check database load
mysql -u root -e "SHOW FULL PROCESSLIST;"

# Check resource usage
top -p $(pgrep -f uvicorn)
df -h
free -m
```

### Unauthorized Access Attempt

```bash
# Check audit logs
mysql -u root dataflow -e "SELECT * FROM audit_logs WHERE action LIKE '%unauthorized%' ORDER BY created_at DESC LIMIT 20;"

# Check for brute force
mysql -u root dataflow -e "SELECT email, failed_login_count, locked_until FROM users WHERE failed_login_count > 0;"

# If active attack:
# 1. Block IP at firewall level
# 2. Force-lock affected accounts
# 3. Rotate JWT secret if compromise suspected
```

## Rollback Procedure

### Application Rollback

```bash
# If using Docker:
docker-compose down
docker-compose -f docker-compose.prod.yml up -d --pull never  # uses previous image

# If using Git:
git log --oneline -5  # find the last good commit
git checkout <good-commit>
# Rebuild and restart
```

### Database Rollback

```bash
# Downgrade one migration
alembic downgrade -1

# Or restore from backup
gunzip -c /path/to/backup.sql.gz | mysql -u root dataflow

# Verify
alembic current
```

## Post-Incident

1. **Timeline:** Document what happened and when
2. **Root Cause:** Identify why it happened
3. **Impact:** How many users/orgs affected
4. **Resolution:** What was done to fix it
5. **Prevention:** What changes prevent recurrence
6. **Action Items:** Assign follow-up tasks

## Emergency Contacts

| Role | Responsibility |
|------|----------------|
| On-call engineer | First response, triage |
| Database admin | MySQL issues, backup/restore |
| Security lead | Auth issues, data breach |
| Product owner | User communication, severity assessment |

## Useful Commands Quick Reference

```bash
# Restart application
systemctl restart dataflow-api

# Check health
curl localhost:8001/health

# Database backup (emergency)
mysqldump --single-transaction dataflow | gzip > emergency_$(date +%s).sql.gz

# View active connections
mysql -e "SHOW PROCESSLIST;"

# Kill long-running query
mysql -e "KILL <process_id>;"

# Check disk space
df -h

# Check memory
free -m

# View recent logs
tail -100 /var/log/dataflow/app.log
```
