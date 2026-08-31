"""Check production Hostinger MySQL schema for drift audit."""

import pymysql

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

conn = pymysql.connect(
    host=host, port=port, user=user, password=pw, database=db, connect_timeout=10
)
cur = conn.cursor()

# 1. Check capture_documents indexes
cur.execute("SHOW INDEX FROM capture_documents")
indexes = [r[2] for r in cur.fetchall()]
print("capture_documents indexes:", sorted(set(indexes)))
print("ix_capture_documents_org_type present:", "ix_capture_documents_org_type" in indexes)
print("ix_capture_documents_org_status present:", "ix_capture_documents_org_status" in indexes)

# 2. Check key tables exist
for table in [
    "workspaces",
    "invitations",
    "dataset_workflow_runs",
    "background_jobs",
    "capture_documents",
    "capture_fields",
    "capture_batches",
]:
    cur.execute(f"SHOW TABLES LIKE '{table}'")
    print(f"{table} table exists:", cur.fetchone() is not None)

# 3. Check all tables in production
cur.execute("SHOW TABLES")
all_tables = [r[0] for r in cur.fetchall()]
print(f"\nTotal tables in production: {len(all_tables)}")
print("Tables:", sorted(all_tables))

cur.close()
conn.close()
print("\nSUCCESS: Production schema check complete")
