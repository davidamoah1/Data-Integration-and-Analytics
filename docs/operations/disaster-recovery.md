# Disaster Recovery

> **Version**: 1.0.0  
> **Last Updated**: 2026-07-30  
> **Status**: Active  
> **Owner**: DevOps Engineer

---

## Purpose

Disaster recovery plan for major incidents.

## Scope

Recovery procedures for database failure, application failure, and data loss.

## Audience

DevOps engineers, CTO, and operations team.

---

## 1. Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Database failure | 2 hours | 24 hours |
| Application failure | 30 minutes | 0 (stateless) |
| Data center failure | 4 hours | 24 hours |
| Data corruption | 4 hours | 24 hours |

- **RTO**: Recovery Time Objective — max time to restore
- **RPO**: Recovery Point Objective — max data loss tolerance

## 2. Recovery Procedures

### Database Failure

1. Provision new PostgreSQL instance
2. Restore from most recent backup:
   ```bash
   psql $NEW_DATABASE_URL < backup_YYYYMMDD.sql
   ```
3. Update `DATABASE_URL` environment variable
4. Restart application
5. Verify health check passes
6. Verify data integrity (table counts, latest records)

### Application Failure

1. Identify failure cause (check logs)
2. Rollback to previous deployment (Vercel: redeploy previous commit)
3. Verify health check passes
4. Monitor for recurrence

### Data Corruption

1. Identify corrupted tables/records
2. Restore from backup to test database
3. Compare and identify corrupted data
4. Restore affected tables from backup
5. Verify data integrity
6. Audit log all recovery actions

## 3. Disaster Recovery Checklist

- [ ] Backup available and verified
- [ ] New database provisioned
- [ ] `DATABASE_URL` updated
- [ ] Application restarted
- [ ] Health check passes
- [ ] Login works
- [ ] Data integrity verified
- [ ] Audit logs intact
- [ ] Stakeholders notified
- [ ] Post-mortem scheduled

## 4. Communication Plan

| Timeframe | Action |
|-----------|--------|
| T+0 | Detect and acknowledge incident |
| T+15min | Notify CTO and response team |
| T+30min | Notify affected organizations |
| T+1hr | Status update to all users |
| T+resolution | Incident resolved notification |
| T+48hr | Post-mortem published |

## Related Documents

- [backups.md](backups.md) — Backup procedures
- [../database/backup-recovery.md](../database/backup-recovery.md) — Database backup
- [incident-response.md](incident-response.md) — Incident response
