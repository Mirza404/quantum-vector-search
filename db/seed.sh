#!/usr/bin/env bash
# Resets the DB to the seed state, safely handling a DB that is ahead of the seed.
#
# Flow:
#   1. Find the highest migration recorded in the seed file.
#   2. Roll back any migrations above that point using down migrations.
#   3. Load the seed (TRUNCATE + INSERT).
#   4. Apply any pending up migrations (catches up if seed is behind HEAD).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/.env" ] && { set -a; source "$SCRIPT_DIR/.env"; set +a; }

DB_CONTAINER="${DB_CONTAINER:-qvs-postgres}"
DB_USER="${DB_USER:-qvs}"
DB_NAME="${DB_NAME:-qvs_benchmarks}"

SEED_FILE="$SCRIPT_DIR/seeds/seed.sql"

# Find the highest migration number recorded in the seed's schema_migrations data.
LAST_N=$(grep -oP "VALUES \('\K\d+(?=_[^']+\.sql')" "$SEED_FILE" | sort -n | tail -1 || true)
LAST_N="${LAST_N:-0}"

if [ "$LAST_N" -gt 0 ]; then
    echo "Seed state: migrations up to #$LAST_N - rolling back anything above that..."
    bash "$SCRIPT_DIR/migrate.sh" down "$LAST_N"
fi

echo "Loading seed..."
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 < "$SEED_FILE"

echo "Applying pending migrations..."
bash "$SCRIPT_DIR/migrate.sh" up
