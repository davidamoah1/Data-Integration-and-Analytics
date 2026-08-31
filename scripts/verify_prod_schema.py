"""Verify production Hostinger MySQL schema after migration."""

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

# 1. Check alembic version
cur.execute("SELECT version_num FROM alembic_version")
version = cur.fetchone()[0]
print(f"Alembic version: {version}")
assert version == "b3c4d5e6f7a8", f"Expected b3c4d5e6f7a8, got {version}"
print("PASS: Alembic version is at head (b3c4d5e6f7a8)")

# 2. Check background_jobs columns
cur.execute("SHOW COLUMNS FROM background_jobs")
cols = [r[0] for r in cur.fetchall()]
print(f"\nbackground_jobs columns: {cols}")
assert "idempotency_key" in cols, "idempotency_key column missing!"
print("PASS: idempotency_key column exists")

# 3. Check background_jobs indexes
cur.execute("SHOW INDEX FROM background_jobs")
indexes = [r[2] for r in cur.fetchall()]
print(f"\nbackground_jobs indexes: {sorted(set(indexes))}")
assert any("idempotency" in i.lower() for i in indexes), "idempotency index missing!"
print("PASS: ix_background_jobs_idempotency_key index exists")

# 4. Check capture_documents composite indexes
cur.execute("SHOW INDEX FROM capture_documents")
cd_indexes = [r[2] for r in cur.fetchall()]
print(f"\ncapture_documents indexes: {sorted(set(cd_indexes))}")
assert "ix_capture_documents_org_type" in cd_indexes, "ix_capture_documents_org_type missing!"
assert "ix_capture_documents_org_status" in cd_indexes, "ix_capture_documents_org_status missing!"
print("PASS: ix_capture_documents_org_type index exists")
print("PASS: ix_capture_documents_org_status index exists")

# 5. Check idempotency_key column type
cur.execute("SHOW COLUMNS FROM background_jobs LIKE 'idempotency_key'")
col_info = cur.fetchone()
print(f"\nidempotency_key column definition: {col_info}")
print(f"  Type: {col_info[1]}, Null: {col_info[2]}")

cur.close()
conn.close()
print("\n=== ALL VERIFICATIONS PASSED ===")
