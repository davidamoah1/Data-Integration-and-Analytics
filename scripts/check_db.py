"""Check existing tables in the SQLite database."""

import sqlite3

conn = sqlite3.connect("database/etl_database.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)

for t in tables:
    cursor.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in cursor.fetchall()]
    print(f"  {t}: {cols}")

conn.close()
