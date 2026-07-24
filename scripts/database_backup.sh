#!/usr/bin/env bash
# database_backup.sh — Automated MySQL backup for AEDIP
# Usage: ./database_backup.sh [backup_dir]
# Cron: 0 2 * * * /path/to/database_backup.sh /path/to/backups

set -euo pipefail

BACKUP_DIR="${1:-backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/aedip_${TIMESTAMP}.sql.gz"

# Load environment variables
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting database backup..."

if [ "${DB_TYPE:-}" = "mysql" ]; then
  MYSQL_PWD="${MYSQL_PASSWORD:-}" mysqldump \
    --single-transaction \
    --routines \
    --triggers \
    --host="${MYSQL_HOST:-localhost}" \
    --port="${MYSQL_PORT:-3306}" \
    --user="${MYSQL_USER:-root}" \
    "${MYSQL_DATABASE:-aedip}" | gzip > "${BACKUP_FILE}"

  if [ $? -eq 0 ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] Backup completed: ${BACKUP_FILE} (${SIZE})"

    # Verify backup
    if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
      echo "[$(date)] Backup verified: OK"
    else
      echo "[$(date)] Backup verification FAILED"
      exit 1
    fi

    # Retention: keep last 30 days
    find "${BACKUP_DIR}" -name "aedip_*.sql.gz" -mtime +30 -delete 2>/dev/null || true
    echo "[$(date)] Old backups cleaned up (30-day retention)"
  else
    echo "[$(date)] Backup FAILED"
    exit 1
  fi
elif [ "${DB_TYPE:-}" = "sqlite" ]; then
  SQLITE_PATH="${SQLITE_DB_PATH:-database/etl_database.db}"
  if [ -f "${SQLITE_PATH}" ]; then
    cp "${SQLITE_PATH}" "${BACKUP_DIR}/aedip_${TIMESTAMP}.db"
    echo "[$(date)] SQLite backup completed: ${BACKUP_DIR}/aedip_${TIMESTAMP}.db"
    find "${BACKUP_DIR}" -name "aedip_*.db" -mtime +30 -delete 2>/dev/null || true
  else
    echo "[$(date)] SQLite database not found: ${SQLITE_PATH}"
    exit 1
  fi
else
  echo "[$(date)] DB_TYPE not set or unsupported: ${DB_TYPE:-}"
  exit 1
fi

echo "[$(date)] Backup process finished."
