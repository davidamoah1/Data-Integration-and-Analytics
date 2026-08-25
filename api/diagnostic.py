"""Minimal diagnostic endpoint for Vercel.

This is a standalone ASGI app that does NOT import the full FastAPI app.
It returns diagnostic info to help identify why the main app returns 500.
"""

import json
import os
import sys
import traceback


async def app(scope, receive, send):
    """ASGI app returning diagnostic info."""
    if scope["type"] != "http":
        return

    info = {
        "python": sys.version,
        "vercel": os.getenv("VERCEL", "not set"),
        "app_env": os.getenv("APP_ENV", "not set"),
        "db_type": os.getenv("DB_TYPE", "not set"),
        "database_url_set": bool(os.getenv("DATABASE_URL", "")),
        "jwt_secret_set": bool(os.getenv("JWT_SECRET_KEY", "")),
        "encryption_key_set": bool(os.getenv("ENCRYPTION_KEY", "")),
        "cors_origins": os.getenv("CORS_ORIGINS", "not set"),
        "storage_backend": os.getenv("STORAGE_BACKEND", "not set"),
    }

    # Try importing config
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config

        info["config_db_type"] = config.DB_TYPE
        info["config_db_url_prefix"] = config.DB_URL[:30] + "..." if config.DB_URL else "not set"
        info["config_is_production"] = config.IS_PRODUCTION
    except Exception as e:
        info["config_error"] = str(e)
        info["config_traceback"] = traceback.format_exc()[-1500:]

    # Try importing the main app
    try:
        from api.main import app as main_app

        info["app_import"] = "success"
    except Exception as e:
        info["app_import"] = "failed"
        info["app_error"] = str(e)
        info["app_traceback"] = traceback.format_exc()[-2000:]

    # Try database connection and check tables
    try:
        from sqlalchemy import create_engine, inspect as sa_inspect
        db_url = config.DB_URL
        eng = create_engine(db_url)
        inspector = sa_inspect(eng)
        all_tables = sorted(inspector.get_table_names())
        info["db_tables"] = all_tables
        required = [
            "users", "roles", "user_roles", "organizations",
            "workspaces", "invitations", "audit_logs", "sessions",
            "departments", "role_permissions",
        ]
        info["db_missing_tables"] = [t for t in required if t not in all_tables]
        eng.dispose()
    except Exception as e:
        info["db_error"] = str(e)
        info["db_traceback"] = traceback.format_exc()[-1500:]

    body = json.dumps(info, indent=2, default=str).encode("utf-8")

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send({"type": "http.response.body", "body": body})
