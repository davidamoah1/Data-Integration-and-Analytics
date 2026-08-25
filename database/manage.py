"""Database management CLI — init, migrate, backup, restore, status.

Usage:
    python -m database.manage init          # Create tables + seed data
    python -m database.manage migrate       # Run Alembic migrations to head
    python -m database.manage backup        # Create a backup
    python -m database.manage restore <file>  # Restore from backup
    python -m database.manage status        # Show DB stats and health
    python -m database.manage indexes       # Ensure critical indexes exist
    python -m database.manage cleanup       # Remove old backups
    python -m database.manage list-backups  # List available backups
"""

from __future__ import annotations

import sys

from shared.database import (
    ensure_default_data,
    ensure_tables,
    get_engine,
    get_session_factory,
    reset_engine,
)


def cmd_init():
    """Create all tables and seed default data."""
    print("Initializing database...")
    engine = get_engine()
    ensure_tables(engine)
    factory = get_session_factory(engine)
    db = factory()
    try:
        ensure_default_data(db)
        db.commit()
        print("✓ Database initialized — tables created and default data seeded.")
    finally:
        db.close()


def cmd_migrate():
    """Run Alembic migrations to head."""
    print("Running Alembic migrations to head...")
    from alembic.config import Config

    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✓ Migrations applied to head.")


def cmd_backup(label: str = ""):
    """Create a database backup."""
    from database.backup import BackupManager

    print("Creating database backup...")
    mgr = BackupManager()
    result = mgr.create_backup(label=label)
    if result.success:
        print(f"✓ Backup created: {result.path}")
        print(f"  Size: {result.size_mb:.2f} MB")
        print(f"  Compressed: {result.compressed}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
    else:
        print(f"✗ Backup failed: {result.error}")
        sys.exit(1)


def cmd_restore(filename: str):
    """Restore database from a backup file."""
    from database.backup import BackupManager

    print(f"Restoring from backup: {filename}")
    mgr = BackupManager()
    result = mgr.restore_backup(filename)
    if result.success:
        print(f"✓ Restore completed in {result.duration_seconds:.2f}s")
        reset_engine()
        print("  Engine cache cleared — restart the application to use the restored data.")
    else:
        print(f"✗ Restore failed: {result.error}")
        sys.exit(1)


def cmd_status():
    """Show database status and health metrics."""
    from sqlalchemy import inspect, text

    engine = get_engine()
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    total_indexes = sum(len(inspector.get_indexes(t)) for t in tables)
    total_cols = sum(len(inspector.get_columns(t)) for t in tables)

    print("┌─ Database Status ─────────────────────────────")
    print(f"│ Environment:  {getattr(__import__('config'), 'APP_ENV', 'unknown')}")
    print(f"│ DB Type:      {getattr(__import__('config'), 'DB_TYPE', 'unknown')}")
    print(f"│ Tables:       {len(tables)}")
    print(f"│ Columns:      {total_cols}")
    print(f"│ Indexes:      {total_indexes}")
    print(f"│ Pool Size:    {getattr(__import__('config'), 'POOL_SIZE', 'N/A')}")
    print(f"│ Max Overflow: {getattr(__import__('config'), 'MAX_OVERFLOW', 'N/A')}")
    print(
        f"│ Slow Query:   {getattr(__import__('config'), 'SLOW_QUERY_THRESHOLD_MS', 'N/A')}ms threshold"
    )
    print(
        f"│ Backup:       {'enabled' if getattr(__import__('config'), 'BACKUP_ENABLED', False) else 'disabled'}"
    )

    # Table details
    if tables:
        print("│")
        print("│ Table Details:")
        with engine.connect() as conn:
            for table in sorted(tables):
                try:
                    count = conn.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).scalar()  # nosec B608 — table from inspector.get_table_names(), not user input
                    idx_count = len(inspector.get_indexes(table))
                    print(f"│   {table:40s} {count:>10} rows  {idx_count:>3} indexes")
                except Exception:
                    print(
                        f"│   {table:40s} {'?':>10} rows  {len(inspector.get_indexes(table)):>3} indexes"
                    )
    print("└─────────────────────────────────────────────────")


def cmd_indexes():
    """Ensure critical indexes exist."""
    from performance.db_optimization import IndexManager

    print("Checking critical indexes...")
    engine = get_engine()
    factory = get_session_factory(engine)
    db = factory()
    try:
        mgr = IndexManager(db)
        result = mgr.ensure_critical_indexes()
        print("✓ Index check complete:")
        print(f"  Created: {len(result['created'])} — {result['created']}")
        print(f"  Skipped: {len(result['skipped'])} (already exist)")
        print(f"  Failed:  {len(result['failed'])}")
    finally:
        db.close()


def cmd_cleanup():
    """Remove old backups beyond retention period."""
    import config
    from database.backup import BackupManager

    print(f"Cleaning up backups older than {config.BACKUP_RETENTION_DAYS} days...")
    mgr = BackupManager()
    result = mgr.cleanup_old_backups()
    print(f"✓ Cleanup complete: deleted {len(result['deleted'])}, kept {len(result['kept'])}")
    if result["deleted"]:
        for name in result["deleted"]:
            print(f"  Deleted: {name}")


def cmd_list_backups():
    """List available backups."""
    from database.backup import BackupManager

    mgr = BackupManager()
    backups = mgr.list_backups()
    if not backups:
        print("No backups found.")
        return

    print(f"{'Filename':50s} {'Size (MB)':>10s} {'Created':25s} {'Compressed':>10s}")
    print("─" * 100)
    for b in backups:
        print(
            f"{b.filename:50s} {b.size_mb:>10.2f} {b.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'):25s} {'yes' if b.compressed else 'no':>10s}"
        )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        "init": cmd_init,
        "migrate": cmd_migrate,
        "backup": cmd_backup,
        "restore": cmd_restore,
        "status": cmd_status,
        "indexes": cmd_indexes,
        "cleanup": cmd_cleanup,
        "list-backups": cmd_list_backups,
    }

    handler = commands.get(cmd)
    if not handler:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

    if cmd == "backup" and args:
        handler(label=args[0])
    elif cmd == "restore":
        if not args:
            print("Usage: python -m database.manage restore <filename>")
            sys.exit(1)
        handler(args[0])
    else:
        handler()


if __name__ == "__main__":
    main()
