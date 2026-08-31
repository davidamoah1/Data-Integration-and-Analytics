"""Comprehensive schema drift audit: SQLAlchemy models vs production MySQL."""

import os
import sys

import pymysql

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Import all models to populate Base.metadata
import config  # noqa
import ai.models  # noqa
import analytics.models  # noqa
import audit.models  # noqa
import authentication.mfa_models  # noqa
import authentication.models  # noqa
import authentication.sso_models  # noqa
import capture.models  # noqa
import connectors.models  # noqa
import database.db_setup  # noqa
import ecosystem.models  # noqa
import ecosystem.plugin_models  # noqa
import ecosystem.webhooks  # noqa
import enterprise.models  # noqa
import enterprise.subscription  # noqa
import etl.models  # noqa
import jobs.models  # noqa
import ml.models  # noqa
import notifications.models  # noqa
import organizations.models  # noqa
import organizations.workspace_models  # noqa
import saas.models  # noqa
import scheduler.models  # noqa
import services.dataset_workflow_models  # noqa
import storage.models  # noqa
import studios.models  # noqa
import validation.models  # noqa
import workflows.models  # noqa
from shared.database import Base  # noqa: E402

# Connect to production MySQL
conn = pymysql.connect(
    host=host, port=port, user=user, password=pw, database=db, connect_timeout=10
)
cur = conn.cursor()

# Get all tables in production
cur.execute("SHOW TABLES")
prod_tables = {r[0] for r in cur.fetchall()}

# Get all tables from models
model_tables = set(Base.metadata.tables.keys())

# 1. Tables in models but not in production
missing_tables = model_tables - prod_tables
print("=" * 70)
print("SCHEMA DRIFT AUDIT: SQLAlchemy Models vs Production MySQL")
print("=" * 70)

print(f"\nModel tables: {len(model_tables)}")
print(f"Production tables: {len(prod_tables)}")

print("\n--- TABLES IN MODELS BUT NOT IN PRODUCTION ---")
if missing_tables:
    for t in sorted(missing_tables):
        print(f"  MISSING: {t}")
else:
    print("  None — all model tables exist in production")

print("\n--- TABLES IN PRODUCTION BUT NOT IN MODELS ---")
extra_tables = prod_tables - model_tables
if extra_tables:
    for t in sorted(extra_tables):
        print(f"  EXTRA: {t}")
else:
    print("  None")

# 2. Check columns for key tables
print("\n--- COLUMN DRIFT CHECK (key tables) ---")
key_tables = [
    "background_jobs",
    "capture_documents",
    "capture_fields",
    "capture_batches",
    "dataset_workflow_runs",
    "users",
    "organizations",
    "audit_logs",
    "file_records",
    "workspaces",
]

drift_found = False
for table_name in key_tables:
    if table_name not in model_tables:
        print(f"\n  {table_name}: NOT IN MODELS (skip)")
        continue
    if table_name not in prod_tables:
        print(f"\n  {table_name}: NOT IN PRODUCTION (skip)")
        continue

    # Get model columns
    model_cols = {c.name for c in Base.metadata.tables[table_name].columns}

    # Get production columns
    cur.execute(f"SHOW COLUMNS FROM `{table_name}`")
    prod_cols = {r[0] for r in cur.fetchall()}

    missing_cols = model_cols - prod_cols
    extra_cols = prod_cols - model_cols

    if missing_cols:
        drift_found = True
        print(f"\n  {table_name}: MISSING COLUMNS IN PRODUCTION:")
        for c in sorted(missing_cols):
            col_type = str(Base.metadata.tables[table_name].columns[c].type)
            print(f"    - {c} ({col_type})")
    if extra_cols:
        print(f"\n  {table_name}: EXTRA COLUMNS IN PRODUCTION (not in models):")
        for c in sorted(extra_cols):
            print(f"    - {c}")
    if not missing_cols and not extra_cols:
        print(f"\n  {table_name}: OK (all columns match)")

# 3. Check indexes for key tables
print("\n--- INDEX DRIFT CHECK (key tables) ---")
for table_name in key_tables:
    if table_name not in model_tables or table_name not in prod_tables:
        continue

    # Get model indexes
    model_indexes = {idx.name for idx in Base.metadata.tables[table_name].indexes if idx.name}

    # Get production indexes
    cur.execute(f"SHOW INDEX FROM `{table_name}`")
    prod_indexes = {r[2] for r in cur.fetchall()}

    missing_idx = model_indexes - prod_indexes
    extra_idx = prod_indexes - model_indexes

    if missing_idx:
        drift_found = True
        print(f"\n  {table_name}: MISSING INDEXES IN PRODUCTION:")
        for i in sorted(missing_idx):
            print(f"    - {i}")
    if extra_idx:
        print(f"\n  {table_name}: EXTRA INDEXES IN PRODUCTION (not in models):")
        for i in sorted(extra_idx):
            print(f"    - {i}")
    if not missing_idx and not extra_idx:
        print(f"\n  {table_name}: OK (all indexes match)")

cur.close()
conn.close()

print("\n" + "=" * 70)
if drift_found:
    print("RESULT: SCHEMA DRIFT DETECTED — see details above")
else:
    print("RESULT: NO SCHEMA DRIFT DETECTED — all key tables match")
print("=" * 70)
