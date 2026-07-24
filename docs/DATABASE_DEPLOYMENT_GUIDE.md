# AEDIP Database Deployment Guide

## Overview

This guide covers deploying AEDIP with MySQL 8 on Hostinger or any MySQL-compatible hosting provider.

## Prerequisites

- MySQL 8.0+ database (Hostinger MySQL or equivalent)
- Python 3.11+ with pip
- `pymysql` driver (`pip install pymysql`)
- Alembic for migrations (`pip install alembic`)

## Step 1: Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Hostinger MySQL credentials:
   ```ini
   DB_TYPE=mysql
   MYSQL_HOST=your-hostinger-mysql-host
   MYSQL_PORT=3306
   MYSQL_DATABASE=u123456789_aedip
   MYSQL_USER=u123456789_aedip_user
   MYSQL_PASSWORD=your-strong-password-here

   # Connection pool
   POOL_SIZE=10
   POOL_TIMEOUT=30
   POOL_RECYCLE=3600
   MAX_OVERFLOW=20

   # Security (MUST change in production)
   JWT_SECRET_KEY=generate-with-openssl-rand-hex-32
   ```

## Step 2: Run Migrations

```bash
# Set environment and run Alembic
alembic upgrade head
```

This creates all database tables in the correct order.

## Step 3: Seed Default Data

```bash
python -c "from database.db_setup import init_db; init_db()"
```

This creates default roles, permissions, and admin user.

## Step 4: Migrate Existing Data (if upgrading from SQLite)

```bash
# Set DB_TYPE=sqlite temporarily, then run migration script
DB_TYPE=sqlite python database/migrate_to_mysql.py
```

The script migrates all tables in dependency order.

## Step 5: Verify Deployment

```bash
# Check database health
python scripts/database_health_check.py

# Check API health
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

## Step 6: Set Up Backups

### Manual Backup
```bash
./scripts/database_backup.sh backups
```

### Automated Daily Backup (cron)
```bash
# Add to crontab (runs daily at 02:00 UTC)
0 2 * * * cd /path/to/aedip && ./scripts/database_backup.sh backups >> logs/backup.log 2>&1
```

### Restore from Backup
```bash
./scripts/database_restore.sh backups/aedip_20260719_020000.sql.gz
```

## Docker Deployment

```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f aedip-api
```

## Hostinger-Specific Notes

1. **Remote MySQL Access**: Enable remote MySQL access in Hostinger hPanel
2. **Connection Limits**: Hostinger shared plans may limit concurrent connections. Adjust `POOL_SIZE` and `MAX_OVERFLOW` accordingly
3. **phpMyAdmin**: Use Hostinger's phpMyAdmin to verify table creation
4. **SSL**: Enable SSL connections by appending `&ssl_ca=/path/to/ca.pem` to the connection URL if required

## Connection Pool Tuning

| Setting | Dev | Staging | Production |
|---------|-----|---------|------------|
| POOL_SIZE | 5 | 10 | 10-20 |
| MAX_OVERFLOW | 10 | 20 | 20-50 |
| POOL_TIMEOUT | 30 | 30 | 30 |
| POOL_RECYCLE | 3600 | 3600 | 1800-3600 |

## Troubleshooting

### Connection Refused
- Verify MySQL host and port in `.env`
- Check firewall rules allow your IP
- Ensure MySQL user has remote access privileges

### Migration Errors
- Run `alembic current` to check migration state
- Run `alembic stamp head` if tables exist but version is unset
- Check `alembic history` for the migration chain

### Pool Exhaustion
- Increase `POOL_SIZE` and `MAX_OVERFLOW`
- Decrease `POOL_RECYCLE` to recycle connections faster
- Check for connection leaks in application logs
