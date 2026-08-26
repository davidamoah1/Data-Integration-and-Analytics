"""Minimal diagnostic endpoint for Vercel.

This is a standalone ASGI app that does NOT import the full FastAPI app.
It returns only non-sensitive diagnostic info to help identify why the main app returns 500.

Security: This endpoint does NOT expose environment variables, database credentials,
table names, column names, stack traces, or any sensitive infrastructure details.
In production, it returns only a minimal status check.
"""

import json
import os
import sys


async def app(scope, receive, send):
    """ASGI app returning minimal, safe diagnostic info."""
    if scope["type"] != "http":
        return

    is_production = os.getenv("APP_ENV", "development").lower() == "production"

    if is_production:
        # In production, return only minimal non-sensitive info
        info = {
            "status": "ok",
            "app_env": os.getenv("APP_ENV", "not set"),
            "db_type": os.getenv("DB_TYPE", "not set"),
            "database_url_set": bool(os.getenv("DATABASE_URL", "")),
            "jwt_secret_set": bool(os.getenv("JWT_SECRET_KEY", "")),
            "encryption_key_set": bool(os.getenv("ENCRYPTION_KEY", "")),
            "storage_backend": os.getenv("STORAGE_BACKEND", "not set"),
        }
    else:
        # In non-production, show more detail for debugging
        info = {
            "python": sys.version,
            "app_env": os.getenv("APP_ENV", "not set"),
            "db_type": os.getenv("DB_TYPE", "not set"),
            "database_url_set": bool(os.getenv("DATABASE_URL", "")),
            "jwt_secret_set": bool(os.getenv("JWT_SECRET_KEY", "")),
            "encryption_key_set": bool(os.getenv("ENCRYPTION_KEY", "")),
            "storage_backend": os.getenv("STORAGE_BACKEND", "not set"),
        }

        # Try importing config (non-sensitive fields only)
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import config

            info["config_db_type"] = config.DB_TYPE
            info["config_is_production"] = config.IS_PRODUCTION
        except Exception as e:
            info["config_error"] = str(e)

        # Try importing the main app
        try:
            from api.main import app  # noqa: F401

            info["app_import"] = "success"
        except Exception as e:
            info["app_import"] = "failed"
            info["app_error"] = str(e)

        # Try database connection (only report connected/not connected)
        try:
            from sqlalchemy import create_engine, text

            import config

            eng = create_engine(config.DB_URL)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            info["db_connected"] = True
            eng.dispose()
        except Exception as e:
            info["db_connected"] = False
            info["db_error"] = str(e)

    body = json.dumps(info, indent=2, default=str).encode("utf-8")

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send({"type": "http.response.body", "body": body})
