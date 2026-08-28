#!/bin/bash
# Run Alembic migrations against the configured database.
# Usage: ./scripts/migrate.sh
# On Render: set as a pre-deploy hook or run via shell.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete."

# Verify migration version
alembic current
