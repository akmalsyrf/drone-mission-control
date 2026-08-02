#!/usr/bin/env bash
# Wait for Postgres/Redis then print stack status.
set -euo pipefail
echo "Compose services:"
docker compose ps
echo
curl -sf http://localhost/api/v1/health | python -m json.tool || true
