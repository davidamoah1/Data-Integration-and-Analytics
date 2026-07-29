# Operations Manual

## Daily Operations

### Health Monitoring

```bash
# Check backend health
curl https://api.yourdomain.com/health

# Check database connectivity
mysql -u root -p -e "SELECT 1"

# Check disk space
df -h

# Check service status
sudo systemctl status dataflow
```

### Log Review

```bash
# Application logs
journalctl -u dataflow --since "1 hour ago"

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log
```

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | Platform down | 15 minutes |
| P1 | Major feature broken | 1 hour |
| P2 | Minor feature broken | 4 hours |
| P3 | Cosmetic issue | 24 hours |

### P0: Platform Down

1. Check if VPS is running: `ssh user@vps`
2. Check service: `sudo systemctl status dataflow`
3. Restart if needed: `sudo systemctl restart dataflow`
4. Check database: `mysql -u root -p -e "SELECT 1"`
5. Check disk: `df -h`
6. Check logs: `journalctl -u dataflow --since "30 min ago"`
7. Notify users via system announcement

### P1: Database Issues

1. Check MySQL status: `sudo systemctl status mysql`
2. Check connections: `mysql -u root -p -e "SHOW PROCESSLIST"`
3. Restart MySQL: `sudo systemctl restart mysql`
4. Restore from backup if needed

## User Management

### Create Super Admin

```sql
INSERT INTO users (email, password_hash, full_name, organization_id, is_active, is_deleted)
VALUES ('newadmin@example.com', '<hash>', 'New Admin', 1, 1, 0);

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.email = 'newadmin@example.com' AND r.name = 'super_admin';
```

### Suspend Organization

```bash
curl -X POST https://api.yourdomain.com/admin-portal/tenants/{org_id}/suspend \
  -H "Authorization: Bearer <admin-token>"
```

## Backup Procedures

### Database Backup

```bash
# Daily backup
mysqldump -u root -p dataflow > /backups/dataflow_$(date +%Y%m%d).sql

# Compress
gzip /backups/dataflow_$(date +%Y%m%d).sql

# Retain 30 days
find /backups -name "dataflow_*.sql.gz" -mtime +30 -delete
```

### Automated Backup (cron)

```bash
# crontab -e
0 2 * * * mysqldump -u root -p$MYSQL_PASSWORD dataflow | gzip > /backups/dataflow_$(date +\%Y\%m\%d).sql.gz
```

## Performance Monitoring

### Key Metrics

- API response time: < 200ms (p95)
- Database query time: < 100ms (p95)
- Error rate: < 1%
- CPU usage: < 80%
- Memory usage: < 80%
- Disk usage: < 85%

### Check Commands

```bash
# CPU and memory
top -bn1 | head -5

# Disk usage
df -h

# Active connections
ss -tunap | grep :8080 | wc -l
```
