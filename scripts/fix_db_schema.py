"""Add missing columns to the organizations table."""

import sqlite3

conn = sqlite3.connect("database/etl_database.db")
cursor = conn.cursor()

columns_to_add = [
    ("website_url", "VARCHAR(500)"),
    ("business_registration_number", "VARCHAR(100)"),
    ("timezone", "VARCHAR(64) NOT NULL DEFAULT 'UTC'"),
    ("date_format", "VARCHAR(32) NOT NULL DEFAULT 'YYYY-MM-DD'"),
    ("locale", "VARCHAR(16) NOT NULL DEFAULT 'en'"),
    ("branding", "JSON"),
]

existing = {row[1] for row in cursor.execute("PRAGMA table_info(organizations)").fetchall()}

for col_name, col_type in columns_to_add:
    if col_name not in existing:
        cursor.execute(f"ALTER TABLE organizations ADD COLUMN {col_name} {col_type}")
        print(f"Added column: {col_name}")
    else:
        print(f"Column already exists: {col_name}")

conn.commit()
conn.close()
print("Done.")
