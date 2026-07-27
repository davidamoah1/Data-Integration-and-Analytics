"""Vercel serverless function entrypoint.

Vercel Python functions expose the ASGI app through a module-level callable.
This adapter imports the canonical FastAPI application from api.main so the
same application runs locally (uvicorn) and on Vercel.
"""

import os
import sys

# Ensure project root is importable on Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mark serverless mode so lifespan skips heavy startup tasks.
os.environ.setdefault("VERCEL", "1")

from api.main import app  # noqa: E402

# Vercel expects an ASGI-compatible callable named `app` at module level.
__all__ = ["app"]
