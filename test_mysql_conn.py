"""Quick MySQL connection test."""

import pymysql
from sqlalchemy import create_engine, text

DB_URL = "mysql+pymysql://dataflow:DataflowProd2026!@127.0.0.1:3306/dataflow_prod?charset=utf8mb4"

# Test 1: raw pymysql
conn = pymysql.connect(
    host="127.0.0.1",
    port=3306,
    user="dataflow",
    password="DataflowProd2026!",
    database="dataflow_prod",
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
