"""Database management API routes â€” admin-only endpoints for backup, status, and optimization.

All endpoints require the 'system.manage' permission.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from shared.database import get_db
from shared.dependencies import require_permissions
from shared.response import success_response

router = APIRouter(prefix="/api/database", tags=["Database Management"])


@router.get("/status")
async def database_status(
    current_user: dict = Depends(require_permissions("system.manage")),
    db: DbSession = Depends(get_db),
):
    """Get database status â€” table counts, index counts, sizes."""
    from sqlalchemy import inspect, text

    engine = db.bind
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    table_details = []
    total_rows = 0
    total_indexes = 0

    for table in sorted(tables):
        try:
            count = db.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar()  # nosec B608 â€” table from inspector.get_table_names()
        except Exception:
            count = 0
        idx_count = len(inspector.get_indexes(table))
        col_count = len(inspector.get_columns(table))
        total_rows += count
        total_indexes += idx_count
        table_details.append(
            {
                "name": table,
                "rows": count,
                "columns": col_count,
                "indexes": idx_count,
            }
        )

    import config

    return success_response(
        {
            "environment": config.APP_ENV,
            "db_type": config.DB_TYPE,
            "pool_size": config.POOL_SIZE,
            "max_overflow": config.MAX_OVERFLOW,
            "slow_query_threshold_ms": config.SLOW_QUERY_THRESHOLD_MS,
            "backup_enabled": config.BACKUP_ENABLED,
            "total_tables": len(tables),
            "total_rows": total_rows,
            "total_indexes": total_indexes,
            "tables": table_details,
        }
    )


@router.post("/backup")
async def create_backup(
    label: str = Query("", description="Optional label for the backup"),
    current_user: dict = Depends(require_permissions("system.manage")),
):
    """Create a database backup."""
    from database.backup import BackupManager

    mgr = BackupManager()
    result = mgr.create_backup(label=label)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return success_response(result.to_dict(), "Backup created successfully")


@router.get("/backups")
async def list_backups(
    current_user: dict = Depends(require_permissions("system.manage")),
):
    """List all available database backups."""
    from database.backup import BackupManager

    mgr = BackupManager()
    backups = mgr.list_backups()
    return success_response(
        [b.to_dict() for b in backups],
        f"Found {len(backups)} backups",
    )


@router.post("/restore")
async def restore_backup(
    filename: str = Query(..., description="Backup filename to restore"),
    current_user: dict = Depends(require_permissions("system.manage")),
):
    """Restore database from a backup file."""
    from database.backup import BackupManager

    mgr = BackupManager()
    result = mgr.restore_backup(filename)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return success_response(result.to_dict(), "Backup restored successfully")


@router.delete("/backups/cleanup")
async def cleanup_backups(
    retention_days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_permissions("system.manage")),
):
    """Delete backups older than the retention period."""
    from database.backup import BackupManager

    mgr = BackupManager()
    result = mgr.cleanup_old_backups(retention_days=retention_days)
    return success_response(result, f"Deleted {len(result['deleted'])} old backups")


@router.post("/indexes")
async def ensure_indexes(
    current_user: dict = Depends(require_permissions("system.manage")),
    db: DbSession = Depends(get_db),
):
    """Ensure all critical database indexes exist."""
    from performance.db_optimization import IndexManager

    mgr = IndexManager(db)
    result = mgr.ensure_critical_indexes()
    return success_response(result, "Index check complete")


@router.get("/backups/{filename}/verify")
async def verify_backup(
    filename: str,
    current_user: dict = Depends(require_permissions("system.manage")),
):
    """Verify a backup file's integrity."""
    from database.backup import BackupManager

    mgr = BackupManager()
    result = mgr.verify_backup(filename)
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result.get("error", "Invalid backup"))
    return success_response(result, "Backup verified")
