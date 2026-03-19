#!/usr/bin/env bash
# Dumps all table data into db/seeds/benchmark_results.sql.
# Commit the result so other contributors get your latest data on their next pull.
# Usage: bash db/dump.sh
#        make db-dump

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/.env" ] && { set -a; source "$SCRIPT_DIR/.env"; set +a; }

DB_CONTAINER="${DB_CONTAINER:-qvs-postgres}"
DB_USER="${DB_USER:-qvs}"
DB_NAME="${DB_NAME:-qvs_benchmarks}"
OUT="$SCRIPT_DIR/seeds/benchmark_results.sql"

# Build a comma-separated list of all data tables (everything except schema_migrations).
TABLES=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT string_agg(tablename, ', ' ORDER BY tablename)
     FROM pg_tables
     WHERE schemaname = 'public';")

cat > "$OUT" <<HEADER
-- Source of truth for all table data. make db-seed resets the DB to this state.
-- Update by running: make db-dump

TRUNCATE TABLE $TABLES RESTART IDENTITY;

HEADER

docker exec "$DB_CONTAINER" pg_dump \
    -U "$DB_USER" -d "$DB_NAME" \
    --data-only \
    --inserts \
    --on-conflict-do-nothing \
    --no-comments \
    >> "$OUT"

echo "Dumped all tables → $OUT"
echo "Commit this file to share your results with the team."
