#!/usr/bin/env bash
# Start SAFIA admin dashboard on a production server (Gunicorn).
#
# Optional environment:
#   ADMIN_DASHBOARD_BIND  host:port (default 0.0.0.0:5454). Use 127.0.0.1:5454 behind nginx.
#   GUNICORN_WORKERS      worker processes (default 2)
#
# Example:
#   ./scripts/start_admin_dashboard_prod.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ADMIN_DASHBOARD_BIND="${ADMIN_DASHBOARD_BIND:-0.0.0.0:5454}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"

exec uv run --group prod gunicorn \
  --bind "${ADMIN_DASHBOARD_BIND}" \
  --workers "${GUNICORN_WORKERS}" \
  --access-logfile - \
  --error-logfile - \
  admin_dashboard:app
