"""Quick MySQL connection test.

Reads connection parameters from environment variables — never hard-codes credentials.
Usage: set MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD env vars.
"""

import os
import sys
from urllib.parse import quote_plus

import pymysql
from sqlalchemy import create_engine, text

_host = os.getenv("MYSQL_HOST", "localhost")
_port = int(os.getenv("MYSQL_PORT", "3306"))
_db = os.getenv("MYSQL_DATABASE", "")
_user = os.getenv("MYSQL_USER", "")
_pass = os.getenv("MYSQL_PASSWORD", "")

if not _db or not _user:
    print("ERROR: MYSQL_DATABASE and MYSQL_USER environment variables must be set.")
    sys.exit(1)

DB_URL = (
    f"mysql+pymysql://{quote_plus(_user)}:{quote_plus(_pass)}"
    f"@{_host}:{_port}/{quote_plus(_db)}?charset=utf8mb4"
)

# Test 1: raw pymysql
conn = pymysql.connect(
    host=_host,
    port=_port,
    user=_user,
    password=_pass,
    database=_db,
)
cur = conn.cursor()
cur.execute("SELECT VERSION()")
ver = cur.fetchone()
print(f"pymysql direct: {ver}")
conn.close()

# Test 2: SQLAlchemy
engine = create_engine(DB_URL)
with engine.connect() as c:
    result = c.execute(text("SELECT VERSION()")).fetchone()
    print(f"SQLAlchemy: {result}")
print("All connection tests passed.")
