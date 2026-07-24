#!/usr/bin/env bash
# database_restore.sh — Restore AEDIP database from backup
# Usage: ./database_restore.sh <backup_file>

set -euo pipefail

BACKUP_FILE="${1:-}"

if [ -z "${BACKUP_FILE}" ]; then
  echo "Usage: $0 <backup_file>"
  echo "Example: $0 backups/aedip_20260719_020000.sql.gz"
  exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Error: Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

# Load environment variables
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

echo "[$(date)] Starting database restore from: ${BACKUP_FILE}"

if [ "${DB_TYPE:-}" = "mysql" ]; then
  echo "[$(date)] Restoring to MySQL: ${MYSQL_HOST:-localhost}:${MYSQL_PORT:-3306}/${MYSQL_DATABASE:-aedip}"

  # Decompress and pipe to mysql
  gunzip -c "${BACKUP_FILE}" | MYSQL_PWD="${MYSQL_PASSWORD:-}" mysql \
    --host="${MYSQL_HOST:-localhost}" \
    --port="${MYSQL_PORT:-3306}" \
    --user="${MYSQL_USER:-root}" \
    "${MYSQL_DATABASE:-aedip}"

  if [ $? -eq 0 ]; then
    echo "[$(date)] Restore completed successfully."
    echo "[$(date)] Verifying restore..."

    TABLE_COUNT=$(MYSQL_PWD="${MYSQL_PASSWORD:-}" mysql \
      --host="${MYSQL_HOST:-localhost}" \
      --port="${MYSQL_PORT:-3306}" \
      --user="${MYSQL_USER:-root}" \
      "${MYSQL_DATABASE:-aedip}" \
      -sN -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${MYSQL_DATABASE:-aedip}'")

    echo "[$(date)] Tables in restored database: ${TABLE_COUNT}"
  else
    echo "[$(date)] Restore FAILED"
    exit 1
  fi

elif [ "${DB_TYPE:-}" = "sqlite" ]; then
  SQLITE_PATH="${SQLITE_DB_PATH:-database/etl_database.db}"

  # Backup current database before overwriting
  if [ -f "${SQLITE_PATH}" ]; then
    cp "${SQLITE_PATH}" "${SQLITE_PATH}.pre_restore_$(date +%Y%m%d_%H%M%S)"
    echo "[$(date)] Current database backed up before restore."
  fi

  cp "${BACKUP_FILE}" "${SQLITE_PATH}"
  echo "[$(date)] SQLite restore completed: ${SQLITE_PATH}"

else
  echo "[$(date)] DB_TYPE not set or unsupported: ${DB_TYPE:-}"
  exit 1
fi

echo "[$(date)] Restore process finished."
