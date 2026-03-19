#!/usr/bin/env bash
# Truncates all data tables, leaving schema and migration history intact.
# Usage: bash db/clean.sh
#        make clean

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/.env" ] && { set -a; source "$SCRIPT_DIR/.env"; set +a; }

DB_CONTAINER="${DB_CONTAINER:-qvs-postgres}"
DB_USER="${DB_USER:-qvs}"
DB_NAME="${DB_NAME:-qvs_benchmarks}"

TABLES=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c \
    "SELECT string_agg(tablename, ', ' ORDER BY tablename)
     FROM pg_tables
     WHERE schemaname = 'public' AND tablename != 'schema_migrations';")

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "TRUNCATE TABLE $TABLES RESTART IDENTITY;"

echo "Truncated: $TABLES"
