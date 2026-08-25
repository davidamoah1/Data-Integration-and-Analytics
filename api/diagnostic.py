"""Minimal diagnostic endpoint for Vercel.

This function does NOT import the full FastAPI app. It tests basic
Python functionality and environment configuration on Vercel.
"""

import json
import os
import sys
import traceback


def handler(request):
    """Return diagnostic info as JSON."""
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
        info["config_db_url_set"] = bool(config.DB_URL)
        info["config_is_production"] = config.IS_PRODUCTION
    except Exception as e:
        info["config_error"] = str(e)
        info["config_traceback"] = traceback.format_exc()

    # Try importing the main app
    try:
        from api.main import app

        info["app_import"] = "success"
    except Exception as e:
        info["app_import"] = "failed"
        info["app_error"] = str(e)
        info["app_traceback"] = traceback.format_exc()[-2000:]

    body = json.dumps(info, indent=2, default=str).encode("utf-8")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": body.decode("utf-8"),
    }
