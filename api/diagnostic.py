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
        from api.main import app  # noqa: F401

        info["app_import"] = "success"
    except Exception as e:
        info["app_import"] = "failed"
        info["app_error"] = str(e)
        info["app_traceback"] = traceback.format_exc()[-2000:]

    # Try database connection and check tables
    try:
        from sqlalchemy import create_engine
        from sqlalchemy import inspect as sa_inspect
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

    # Try a test signup flow to capture the exact error
    try:
        from sqlalchemy import create_engine as _ce
        from sqlalchemy.orm import sessionmaker as _sm
        eng = _ce(config.DB_URL)

        # Run ensure_tables to add missing columns/tables
        from shared.database import ensure_default_data, ensure_tables
        ensure_tables(eng)

        SessionLocal = _sm(bind=eng, expire_on_commit=False)
        db = SessionLocal()

        # Check if default roles exist
        from sqlalchemy import text as _text
        roles = db.execute(_text("SELECT id, name FROM roles")).fetchall()
        info["db_roles"] = [{"id": r[0], "name": r[1]} for r in roles]

        # Check users table columns
        from sqlalchemy import inspect as _insp
        insp = _insp(eng)
        user_cols = [c["name"] for c in insp.get_columns("users")]
        info["db_user_columns"] = user_cols

        # Seed default data (roles, permissions)
        ensure_default_data(db)
        db.commit()

        # Re-check roles after seeding
        roles = db.execute(_text("SELECT id, name FROM roles")).fetchall()
        info["db_roles_after_seed"] = [{"id": r[0], "name": r[1]} for r in roles]

        # Try the actual registration service
        from organizations.invitation_schemas import SignupV2Request
        from organizations.invitation_service import RegistrationService
        test_req = SignupV2Request(
            email="diag_test@test.com",
            password="TestPass123!",
            full_name="Diag Test",
            registration_mode="create_organization",
            organization_name="Diag Test Org",
            country="US",
            industry="tech",
            organization_type="startup",
        )
        svc = RegistrationService(db)
        result = svc.register(test_req)
        info["signup_test"] = "success"
        info["signup_result"] = {k: v for k, v in result.items() if k != "access_token" and k != "refresh_token"}
        # Clean up test data
        db.rollback()
        db.close()
        eng.dispose()
    except Exception as e:
        info["signup_test"] = "failed"
        info["signup_error"] = str(e)
        info["signup_traceback"] = traceback.format_exc()[-2500:]
        try:
            db.rollback()
            db.close()
            eng.dispose()
        except Exception:
            pass

    body = json.dumps(info, indent=2, default=str).encode("utf-8")

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send({"type": "http.response.body", "body": body})
