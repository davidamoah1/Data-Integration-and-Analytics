"""Backup and restore verification service.

Provides scheduled and on-demand backups of the application database and
critical configuration. Supports SQLite (file copy) and MySQL (mysqldump).
"""

from __future__ import annotations

import contextlib
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from etl.logging_config import logger


def _backup_dir() -> Path:
    """Return the configured backup directory, creating it lazily when needed.

    In serverless/readonly environments the directory creation is skipped if
    the filesystem is not writable; callers must handle the resulting error.
    """
    base = Path(__file__).resolve().parent.parent
    path = base / os.getenv("BACKUP_PATH", "backups")
    # Only create the directory when we are actually about to write a backup.
    return path


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


class BackupService:
    """Create, list, and verify backups of the AEDIP database and config."""

    def __init__(self, backup_root: str | Path | None = None) -> None:
        self.backup_root = Path(backup_root) if backup_root else _backup_dir()
        # Do not fail construction on read-only filesystems; create lazily on demand.
        with contextlib.suppress(OSError):
            self.backup_root.mkdir(parents=True, exist_ok=True)

    def create_backup(self, name: str | None = None) -> dict[str, Any]:
        """Create a timestamped database and configuration backup.

        Returns:
            Dict with backup id, paths, size bytes, and verification status.
        """
        import config

        try:
            self.backup_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return {
                "id": _timestamp(),
                "status": "failed",
                "error": f"Backup directory not writable: {e}",
                "verified": False,
            }

        ts = _timestamp()
        label = f"{name}_" if name else ""
        backup_id = f"{label}{ts}"
        backup_path = self.backup_root / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)

        db_result = self._backup_database(config, backup_path)
        config_result = self._backup_config(backup_path)

        total_size = sum(f.stat().st_size for f in backup_path.rglob("*") if f.is_file())
        verified = db_result["verified"] and config_result["verified"]

        result = {
            "id": backup_id,
            "path": str(backup_path),
            "size_bytes": total_size,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database": db_result,
            "config": config_result,
            "verified": verified,
        }
        logger.info("Backup %s created: verified=%s size=%s", backup_id, verified, total_size)
        return result

    def _backup_database(self, config_module: Any, backup_path: Path) -> dict[str, Any]:
        db_type = getattr(config_module, "DB_TYPE", "sqlite")
        db_file = backup_path / f"db_{db_type}.backup"

        if db_type == "sqlite":
            db_url = getattr(config_module, "DB_URL", "")
            db_file_source = db_url.replace("sqlite:///", "").lstrip("/")
            if not db_file_source or not Path(db_file_source).exists():
                return {
                    "status": "skipped",
                    "path": None,
                    "verified": False,
                    "error": "SQLite source not found",
                }
            shutil.copy2(db_file_source, db_file)
            return {
                "status": "completed",
                "path": str(db_file),
                "verified": self._verify_sqlite(db_file),
            }

        if db_type == "mysql":
            host = os.getenv("MYSQL_HOST", "localhost")
            port = os.getenv("MYSQL_PORT", "3306")
            database = os.getenv("MYSQL_DATABASE", "")
            user = os.getenv("MYSQL_USER", "")
            password = os.getenv("MYSQL_PASSWORD", "")
            try:
                env = os.environ.copy()
                if password:
                    env["MYSQL_PWD"] = password
                cmd = [
                    "mysqldump",
                    "--single-transaction",
                    "--host",
                    host,
                    "--port",
                    str(port),
                    "--user",
                    user,
                    "--databases",
                    database,
                ]
                with open(db_file, "w", encoding="utf-8") as f:
                    subprocess.run(cmd, env=env, stdout=f, check=True, text=True, timeout=300)
                return {
                    "status": "completed",
                    "path": str(db_file),
                    "verified": db_file.exists() and db_file.stat().st_size > 0,
                }
            except Exception as exc:
                logger.exception("MySQL backup failed: %s", exc)
                return {"status": "failed", "path": None, "verified": False, "error": str(exc)}

        return {"status": "unsupported", "path": None, "verified": False}

    def _backup_config(self, backup_path: Path) -> dict[str, Any]:
        base = Path(__file__).resolve().parent.parent
        env_source = base / ".env"
        config_backup = backup_path / "env.backup"
        try:
            if env_source.exists():
                shutil.copy2(env_source, config_backup)
                return {
                    "status": "completed",
                    "path": str(config_backup),
                    "verified": config_backup.exists(),
                }
            return {"status": "skipped", "path": None, "verified": True, "reason": ".env not found"}
        except OSError as e:
            return {"status": "failed", "path": None, "verified": False, "error": str(e)}

    @staticmethod
    def _verify_sqlite(db_file: Path) -> bool:
        try:
            conn = sqlite3.connect(str(db_file))
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            conn.close()
            return True
        except Exception as exc:
            logger.error("SQLite backup verification failed: %s", exc)
            return False

    def list_backups(self) -> list[dict[str, Any]]:
        """Return metadata for each backup directory."""
        backups = []
        for path in sorted(self.backup_root.iterdir()):
            if not path.is_dir():
                continue
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            backups.append(
                {
                    "id": path.name,
                    "path": str(path),
                    "size_bytes": size,
                    "created_at": datetime.fromtimestamp(
                        path.stat().st_ctime, tz=timezone.utc
                    ).isoformat(),
                }
            )
        return backups
