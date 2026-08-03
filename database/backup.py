"""Database backup and recovery utilities.

Provides:
  - BackupManager: Create, list, verify, and restore database backups
  - Supports both MySQL (mysqldump) and SQLite (file copy) backends
  - Automatic retention-based cleanup of old backups
  - Backup verification via integrity checks

Usage:
    from database.backup import BackupManager

    mgr = BackupManager()
    result = mgr.create_backup()
    print(result)  # {"path": "...", "size_mb": 12.3, "compressed": True}

    # List available backups
    backups = mgr.list_backups()

    # Restore from a backup
    mgr.restore_backup("backup_20260801_020000.sql.gz")

    # Clean old backups (retention-based)
    mgr.cleanup_old_backups()
"""

from __future__ import annotations

import gzip
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import config

logger = logging.getLogger("database.backup")


@dataclass
class BackupInfo:
    """Metadata for a single backup file."""

    filename: str
    path: str
    size_mb: float
    created_at: datetime
    compressed: bool

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "path": self.path,
            "size_mb": round(self.size_mb, 2),
            "created_at": self.created_at.isoformat(),
            "compressed": self.compressed,
        }


@dataclass
class BackupResult:
    """Result of a backup operation."""

    success: bool
    path: str = ""
    size_mb: float = 0.0
    compressed: bool = False
    error: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "path": self.path,
            "size_mb": round(self.size_mb, 2),
            "compressed": self.compressed,
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 2),
        }


class BackupManager:
    """Manages database backups with support for MySQL and SQLite."""

    def __init__(self, backup_dir: str | None = None, compress: bool | None = None):
        self.backup_dir = Path(backup_dir or config.BACKUP_STORAGE_PATH)
        self.compress = compress if compress is not None else config.BACKUP_COMPRESS
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "") -> BackupResult:
        """Create a new database backup.

        Args:
            label: Optional label to include in the backup filename.

        Returns:
            BackupResult with backup details or error information.
        """
        start = datetime.now(timezone.utc)
        timestamp = start.strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""

        if config.DB_TYPE == "mysql":
            return self._backup_mysql(timestamp, suffix, start)
        elif config.DB_TYPE == "sqlite":
            return self._backup_sqlite(timestamp, suffix, start)
        else:
            return BackupResult(success=False, error=f"Unsupported DB_TYPE: {config.DB_TYPE}")

    def _backup_mysql(self, timestamp: str, suffix: str, start: datetime) -> BackupResult:
        """Create a MySQL backup using mysqldump."""
        db_name = os.getenv("MYSQL_DATABASE", "")
        host = os.getenv("MYSQL_HOST", "localhost")
        port = os.getenv("MYSQL_PORT", "3306")
        user = os.getenv("MYSQL_USER", "")
        password = os.getenv("MYSQL_PASSWORD", "")

        filename = f"backup_{timestamp}{suffix}.sql"
        if self.compress:
            filename += ".gz"
        filepath = self.backup_dir / filename

        try:
            cmd = [
                "mysqldump",
                f"--host={host}",
                f"--port={port}",
                f"--user={user}",
                f"--password={password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                "--quick",
                db_name,
            ]

            with open(filepath, "wb") as f:
                if self.compress:
                    # Pipe mysqldump output through gzip
                    dump = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    with gzip.GzipFile(fileobj=f, mode="wb") as gz:
                        shutil.copyfileobj(dump.stdout, gz)
                    dump.wait()
                    if dump.returncode != 0:
                        err = dump.stderr.read().decode()
                        filepath.unlink(missing_ok=True)
                        return BackupResult(success=False, error=f"mysqldump failed: {err}")
                else:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        err = result.stderr.decode()
                        filepath.unlink(missing_ok=True)
                        return BackupResult(success=False, error=f"mysqldump failed: {err}")

            size_mb = filepath.stat().st_size / (1024 * 1024)
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info("MySQL backup created: %s (%.2f MB)", filename, size_mb)
            return BackupResult(
                success=True,
                path=str(filepath),
                size_mb=size_mb,
                compressed=self.compress,
                duration_seconds=duration,
            )
        except FileNotFoundError:
            return BackupResult(success=False, error="mysqldump not found. Install MySQL client tools.")
        except Exception as e:
            filepath.unlink(missing_ok=True)
            return BackupResult(success=False, error=str(e))

    def _backup_sqlite(self, timestamp: str, suffix: str, start: datetime) -> BackupResult:
        """Create a SQLite backup by copying the database file."""
        db_path = config.DB_URL.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            return BackupResult(success=False, error=f"SQLite database not found: {db_path}")

        filename = f"backup_{timestamp}{suffix}.db"
        if self.compress:
            filename += ".gz"
        filepath = self.backup_dir / filename

        try:
            if self.compress:
                with open(db_path, "rb") as src, gzip.GzipFile(filepath, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            else:
                shutil.copy2(db_path, filepath)

            size_mb = filepath.stat().st_size / (1024 * 1024)
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info("SQLite backup created: %s (%.2f MB)", filename, size_mb)
            return BackupResult(
                success=True,
                path=str(filepath),
                size_mb=size_mb,
                compressed=self.compress,
                duration_seconds=duration,
            )
        except Exception as e:
            filepath.unlink(missing_ok=True)
            return BackupResult(success=False, error=str(e))

    def list_backups(self) -> list[BackupInfo]:
        """List all available backups, sorted by date (newest first)."""
        backups = []
        for entry in self.backup_dir.iterdir():
            if not entry.is_file():
                continue
            if not (entry.name.startswith("backup_") and (entry.suffix in (".sql", ".gz", ".db"))):
                continue
            stat = entry.stat()
            backups.append(BackupInfo(
                filename=entry.name,
                path=str(entry),
                size_mb=stat.st_size / (1024 * 1024),
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                compressed=entry.name.endswith(".gz"),
            ))
        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups

    def restore_backup(self, filename: str) -> BackupResult:
        """Restore database from a backup file.

        Args:
            filename: Name of the backup file in the backup directory.

        Returns:
            BackupResult with restore details or error.
        """
        filepath = self.backup_dir / filename
        if not filepath.exists():
            return BackupResult(success=False, error=f"Backup file not found: {filename}")

        start = datetime.now(timezone.utc)

        if config.DB_TYPE == "mysql":
            return self._restore_mysql(filepath, start)
        elif config.DB_TYPE == "sqlite":
            return self._restore_sqlite(filepath, start)
        else:
            return BackupResult(success=False, error=f"Unsupported DB_TYPE: {config.DB_TYPE}")

    def _restore_mysql(self, filepath: Path, start: datetime) -> BackupResult:
        """Restore a MySQL backup."""
        db_name = os.getenv("MYSQL_DATABASE", "")
        host = os.getenv("MYSQL_HOST", "localhost")
        port = os.getenv("MYSQL_PORT", "3306")
        user = os.getenv("MYSQL_USER", "")
        password = os.getenv("MYSQL_PASSWORD", "")

        try:
            cmd = [
                "mysql",
                f"--host={host}",
                f"--port={port}",
                f"--user={user}",
                f"--password={password}",
                db_name,
            ]

            if filepath.name.endswith(".gz"):
                with gzip.open(filepath, "rb") as f:
                    result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE)
            else:
                with open(filepath, "rb") as f:
                    result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE)

            if result.returncode != 0:
                err = result.stderr.decode()
                return BackupResult(success=False, error=f"mysql restore failed: {err}")

            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info("MySQL backup restored: %s", filepath.name)
            return BackupResult(success=True, path=str(filepath), duration_seconds=duration)
        except FileNotFoundError:
            return BackupResult(success=False, error="mysql client not found. Install MySQL client tools.")
        except Exception as e:
            return BackupResult(success=False, error=str(e))

    def _restore_sqlite(self, filepath: Path, start: datetime) -> BackupResult:
        """Restore a SQLite backup."""
        db_path = config.DB_URL.replace("sqlite:///", "")

        try:
            # Create a pre-restore safety backup
            if os.path.exists(db_path):
                safety = self.backup_dir / f"pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, safety)

            if filepath.name.endswith(".gz"):
                with gzip.open(filepath, "rb") as src, open(db_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            else:
                shutil.copy2(filepath, db_path)

            duration = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info("SQLite backup restored: %s", filepath.name)
            return BackupResult(success=True, path=str(filepath), duration_seconds=duration)
        except Exception as e:
            return BackupResult(success=False, error=str(e))

    def cleanup_old_backups(self, retention_days: int | None = None) -> dict:
        """Delete backups older than the retention period.

        Args:
            retention_days: Override config.BACKUP_RETENTION_DAYS.

        Returns:
            Summary dict with deleted and kept counts.
        """
        days = retention_days or config.BACKUP_RETENTION_DAYS
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
        deleted = []
        kept = []

        for entry in self.backup_dir.iterdir():
            if not entry.is_file() or not entry.name.startswith("backup_"):
                continue
            if entry.stat().st_mtime < cutoff:
                entry.unlink()
                deleted.append(entry.name)
            else:
                kept.append(entry.name)

        logger.info("Backup cleanup: deleted %d, kept %d", len(deleted), len(kept))
        return {"deleted": deleted, "kept": kept, "retention_days": days}

    def verify_backup(self, filename: str) -> dict:
        """Verify a backup file's integrity.

        Args:
            filename: Name of the backup file to verify.

        Returns:
            Dict with verification status.
        """
        filepath = self.backup_dir / filename
        if not filepath.exists():
            return {"valid": False, "error": "File not found"}

        size = filepath.stat().st_size
        if size == 0:
            return {"valid": False, "error": "Empty file"}

        if filepath.name.endswith(".gz"):
            try:
                with gzip.open(filepath, "rb") as f:
                    f.read(1024)  # Try reading a chunk
                return {"valid": True, "size_bytes": size, "compressed": True}
            except Exception as e:
                return {"valid": False, "error": f"Corrupt gzip: {e}"}

        # For non-compressed, just check it's non-empty
        return {"valid": True, "size_bytes": size, "compressed": False}
