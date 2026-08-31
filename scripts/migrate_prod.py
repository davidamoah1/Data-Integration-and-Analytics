"""Run Alembic migration against production Hostinger MySQL.

This script:
1. Reads MySQL credentials from .env (without exposing them)
2. Constructs the SQLAlchemy DATABASE_URL
3. Sets it as an environment variable
4. Runs `alembic upgrade head`
5. Verifies the result

Usage: python scripts/migrate_prod.py
"""

import os
import subprocess
import sys
from urllib.parse import quote_plus

# Read .env for MySQL creds
env = {}
with open(".env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

host = env.get("MYSQL_HOST", "srv1925.hstgr.io")
port = int(env.get("MYSQL_PORT", "3306"))
db = env.get("MYSQL_DATABASE", "")
user = env.get("MYSQL_USER", "")
pw = env.get("MYSQL_PASSWORD", "")

# Construct SQLAlchemy URL for MySQL (pymysql driver) with URL-encoded credentials
db_url = f"mysql+pymysql://{quote_plus(user)}:{quote_plus(pw)}@{host}:{port}/{db}?charset=utf8mb4"

# Set environment variables for Alembic
os.environ["DB_TYPE"] = "mysql"
os.environ["DATABASE_URL"] = db_url
os.environ["APP_ENV"] = "production"

# Required by config.validate_config() for production
jwt_secret = env.get("JWT_SECRET_KEY", "")
os.environ["JWT_SECRET_KEY"] = jwt_secret
os.environ["ENCRYPTION_KEY"] = env.get("ENCRYPTION_KEY", "") or jwt_secret
os.environ["CORS_ORIGINS"] = env.get(
    "CORS_ORIGINS", "https://data-integration-and-analytics.vercel.app"
)
os.environ["STORAGE_BACKEND"] = env.get("STORAGE_BACKEND", "r2")
os.environ["ALLOW_LOCAL_STORAGE_IN_PRODUCTION"] = "1"

# Verify we're NOT pointing at SQLite
assert "sqlite" not in db_url.lower(), "FATAL: Refusing to migrate SQLite database!"
assert "mysql" in db_url.lower(), "FATAL: Not a MySQL database URL!"

print(f"Target database: mysql at {host}:{port}/{db}")
print(f"User: {user}")
print("Password: [REDACTED]")
print()

# Run alembic upgrade head
print("Running: alembic upgrade head")
result = subprocess.run(
    ["alembic", "upgrade", "head"],
    capture_output=True,
    text=True,
    env=os.environ,
)
print("STDOUT:", result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)

if result.returncode != 0:
    print("MIGRATION FAILED!")
    sys.exit(1)

print("\nMigration command completed successfully.")
