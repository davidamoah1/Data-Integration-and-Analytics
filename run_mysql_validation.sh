#!/bin/bash
set -e
source /opt/df_venv/bin/activate
cd /mnt/d/Dataflow

# Ensure MySQL is running
service mysql start 2>/dev/null || true
sleep 5

# Verify MySQL is up
echo "=== MySQL Version ==="
mysql -u root -e "SELECT VERSION();"
echo ""

# Drop and recreate clean database
echo "=== Recreating clean database ==="
mysql -u root -e "DROP DATABASE IF EXISTS dataflow_prod;"
mysql -u root -e "CREATE DATABASE dataflow_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'dataflow'@'%' IDENTIFIED BY 'DataflowProd2026!'; CREATE USER IF NOT EXISTS 'dataflow'@'localhost' IDENTIFIED BY 'DataflowProd2026!'; GRANT ALL PRIVILEGES ON dataflow_prod.* TO 'dataflow'@'%'; GRANT ALL PRIVILEGES ON dataflow_prod.* TO 'dataflow'@'localhost'; FLUSH PRIVILEGES;"
echo "Database recreated."
echo ""

# Set environment for Alembic
export APP_ENV=production
export DATABASE_URL="mysql+pymysql://dataflow:DataflowProd2026!@127.0.0.1:3306/dataflow_prod?charset=utf8mb4"
export JWT_SECRET_KEY="production-validation-secret-key-32chars-min"
export ENCRYPTION_KEY="dGVzdC1lbmNyeXB0aW9uLWtleS1mb3ItdmFsaWRhdGlvbjEyMzQ="
export CORS_ORIGINS="https://app.example.com"
export STORAGE_BACKEND="local"
export ALLOW_LOCAL_STORAGE_IN_PRODUCTION=1
export SEED_DEMO_DATA=false
export DISABLE_CONFIG_VALIDATION=1

# Run Alembic migrations
echo "=== Alembic Migrations ==="
alembic upgrade head 2>&1
echo ""

# Verify single head
echo "=== Alembic Heads ==="
alembic heads 2>&1
echo ""

# Verify current
echo "=== Alembic Current ==="
alembic current 2>&1
echo ""

# Schema verification
echo "=== Schema Verification ==="
/opt/df_venv/bin/python -c "
import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3306, user='dataflow',
                       password='DataflowProd2026!', database='dataflow_prod')
cur = conn.cursor()

# Table count
cur.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'dataflow_prod'\")
table_count = cur.fetchone()[0]
print(f'Tables: {table_count}')

# Foreign keys
cur.execute(\"SELECT COUNT(DISTINCT constraint_name) FROM information_schema.table_constraints WHERE table_schema = 'dataflow_prod' AND constraint_type = 'FOREIGN KEY'\")
fk_count = cur.fetchone()[0]
print(f'Foreign keys: {fk_count}')

# Indexes (non-PK)
cur.execute(\"SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics WHERE table_schema = 'dataflow_prod' AND index_name != 'PRIMARY'\")
idx_count = cur.fetchone()[0]
print(f'Indexes (non-PK): {idx_count}')

# Unique constraints
cur.execute(\"SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = 'dataflow_prod' AND constraint_type = 'UNIQUE'\")
uniq_count = cur.fetchone()[0]
print(f'Unique constraints: {uniq_count}')

# Character set
cur.execute('SELECT @@character_set_database, @@collation_database')
cs = cur.fetchone()
print(f'Character set: {cs[0]}')
print(f'Collation: {cs[1]}')

# Check all tables use utf8mb4
cur.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'dataflow_prod' AND table_collation NOT LIKE 'utf8mb4%'\")
non_utf8mb4 = cur.fetchone()[0]
print(f'Tables NOT using utf8mb4: {non_utf8mb4}')

# Nullable constraints - check for NOT NULL columns
cur.execute(\"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'dataflow_prod' AND is_nullable = 'NO'\")
not_null_count = cur.fetchone()[0]
print(f'NOT NULL columns: {not_null_count}')

# List all tables
cur.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'dataflow_prod' ORDER BY table_name\")
tables = [r[0] for r in cur.fetchall()]
print(f'')
print(f'All {len(tables)} tables:')
for t in tables:
    print(f'  {t}')

conn.close()
"
echo ""

echo "=== ALL SCHEMA CHECKS DONE ==="
