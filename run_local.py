"""Local development startup script.

Sets environment variables for SQLite + CORS + CSP and starts uvicorn.
"""

import os

os.environ["DATABASE_URL"] = ""
os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "database/etl_database.db"
os.environ["PYTEST_RUNNING"] = "1"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"
os.environ["CSP_CONNECT_SRC"] = (
    "http://localhost:3000 http://127.0.0.1:3000 http://localhost:8000 http://127.0.0.1:8000"
)
os.environ["CROSS_ORIGIN_RESOURCE_POLICY"] = "cross-origin"
os.environ["CROSS_ORIGIN_EMBEDDER_POLICY"] = "unsafe-none"
os.environ["DISABLE_CONFIG_VALIDATION"] = "1"

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
