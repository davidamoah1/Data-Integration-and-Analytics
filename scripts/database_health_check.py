#!/usr/bin/env python3
"""Database health check script for AEDIP.

Verifies database connectivity, connection pool status, table integrity,
and storage usage. Exits with code 0 if healthy, 1 if degraded.

Usage:
    python scripts/database_health_check.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json

from monitoring.health_check import run_full_health_check


def main() -> int:
    """Run the full health check and print results."""
    report = run_full_health_check()
    print(json.dumps(report, indent=2, default=str))

    status = report.get("overall_status", "degraded")
    if status == "healthy":
        print("\nâœ… Database health: HEALTHY")
        return 0
    else:
        print("\nâš ï¸  Database health: DEGRADED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
