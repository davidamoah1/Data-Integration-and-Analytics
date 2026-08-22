# MySQL Backup & Recovery

## Backup Strategy

### Automated Backups

The application supports automated backups via environment configuration:

| Setting | Default | Env Var |
|---------|---------|---------|
| Enabled | `false` | `BACKUP_ENABLED` |
| Schedule | `0 2 * * *` (daily 2 AM) | `BACKUP_SCHEDULE` |
| Retention | 30 days | `BACKUP_RETENTION_DAYS` |
| Storage path | `backups/` | `BACKUP_STORAGE_PATH` |
| Compression | `true` | `BACKUP_COMPRESS` |

**Production requirement**: `BACKUP_STORAGE_PATH` must be an absolute path,
not inside the application container's ephemeral filesystem.

### Manual Backup with mysqldump

```bash
# Full database dump (all tables, schema + data)
mysqldump \
  --host=$MYSQL_HOST \
  --port=$MYSQL_PORT \
  --user=$MYSQL_USER \
  --password \
  --single-transaction \
  --routines \
  --triggers \
  --default-character-set=utf8mb4 \
  $MYSQL_DATABASE > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
mysqldump \
  --host=$MYSQL_HOST \
  --port=$MYSQL_PORT \
  --user=$MYSQL_USER \
  --password \
  --single-transaction \
  --routines \
  --triggers \
  --default-character-set=utf8mb4 \
  $MYSQL_DATABASE | gzip > backup_$(date +%Y%m%d).sql.gz

# Schema only (no data)
mysqldump \
  --host=$MYSQL_HOST \
  --port=$MYSQL_PORT \
  --user=$MYSQL_USER \
  --password \
  --no-data \
  --default-character-set=utf8mb4 \
  $MYSQL_DATABASE > schema_$(date +%Y%m%d).sql

# Specific tables only
mysqldump \
  --host=$MYSQL_HOST \
  --port=$MYSQL_PORT \
  --user=$MYSQL_USER \
  --password \
  --single-transaction \
  --default-character-set=utf8mb4 \
  $MYSQL_DATABASE users roles permissions > auth_backup.sql
```

### Key Flags

- `--single-transaction`: InnoDB-consistent snapshot without locking tables.
- `--routines`: Include stored procedures and functions.
- `--triggers`: Include triggers.
- `--default-character-set=utf8mb4`: Ensure correct encoding.

## Backup Verification

```bash
# Verify backup file is not empty
ls -lh backup_*.sql

# Verify it contains expected tables
grep "CREATE TABLE" backup_*.sql | head -20

# Test restore in a throwaway database
mysql -h test-host -u test-user -p test_db < backup_*.sql

# Verify row counts match
mysql -h test-host -u test-user -p test_db -e "
  SELECT 'users' AS tbl, COUNT(*) FROM users
  UNION ALL SELECT 'organizations', COUNT(*) FROM organizations
  UNION ALL SELECT 'sales', COUNT(*) FROM sales;
"
```

## Recovery Procedure

### Full Recovery from Backup

1. **Provision a fresh MySQL 8.4+ instance** with `utf8mb4` charset.

2. **Create the database and user**:
   ```sql
   CREATE DATABASE aedip CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
   CREATE USER 'aedip_user'@'%' IDENTIFIED BY '********';
   GRANT ALL PRIVILEGES ON aedip.* TO 'aedip_user'@'%';
   FLUSH PRIVILEGES;
   ```

3. **Restore from backup**:
   ```bash
   # Uncompressed
   mysql -h new-host -u aedip_user -p aedip < backup_YYYYMMDD.sql

   # Compressed
   gunzip < backup_YYYYMMDD.sql.gz | mysql -h new-host -u aedip_user -p aedip
   ```

4. **Update environment variables** to point to the new instance.

5. **Restart the application**.

6. **Verify health**:
   ```bash
   curl http://localhost:8000/health/db
   ```

7. **Verify data integrity**:
   ```bash
   # Check table counts
   mysql -h new-host -u aedip_user -p aedip -e "SHOW TABLES;"

   # Check migration version
   mysql -h new-host -u aedip_user -p aedip -e "SELECT version_num FROM alembic_version;"
   ```

### Point-in-Time Recovery (Binary Logs)

If binary logging is enabled on MySQL:

```bash
# View available binary logs
mysql -h host -u root -p -e "SHOW BINARY LOGS;"

# Apply binlog events up to a specific timestamp
mysqlbinlog --start-datetime="2025-01-15 10:00:00" \
            --stop-datetime="2025-01-15 14:00:00" \
            /var/lib/mysql/mysql-bin.000123 | mysql -h new-host -u aedip_user -p aedip
```

## Off-Site Backup Storage

### S3-Compatible Storage

```bash
# Upload backup to S3
aws s3 cp backup_$(date +%Y%m%d).sql.gz \
  s3://aedip-backups/$(date +%Y/%m/%d)/backup.sql.gz \
  --storage-class STANDARD_IA

# List backups
aws s3 ls s3://aedip-backups/ --recursive --human-readable
```

### Retention Policy

- Keep daily backups for 30 days
- Keep weekly backups for 12 weeks
- Keep monthly backups for 12 months
- Keep yearly backups indefinitely (or per compliance requirements)

## Disaster Recovery Checklist

- [ ] Backup file available and verified
- [ ] New MySQL 8.4+ instance provisioned
- [ ] `utf8mb4` charset configured
- [ ] Database and user created
- [ ] Backup restored successfully
- [ ] `alembic_version` table shows correct migration
- [ ] Environment variables updated
- [ ] Application restarted
- [ ] Health check passes (`/health/db`)
- [ ] Login works (test with a known account)
- [ ] Data integrity verified (table counts, latest records)
- [ ] DNS/traffic routed to new instance
