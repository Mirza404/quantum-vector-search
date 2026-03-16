#!/usr/bin/env bash
# Dumps benchmark_results from the running qvs-postgres container into data.sql.
# Usage: bash db/dump.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$SCRIPT_DIR/data.sql"

cat > "$OUT" <<'EOF'
-- Placeholder for benchmark_results data exports.
-- Replace this file with:
--   bash db/dump.sh
-- when you need to share the latest rows with the rest of the team.
--
-- The TRUNCATE ensures a clean slate before inserting, so this file is safe to re-run.
TRUNCATE TABLE benchmark_results RESTART IDENTITY;

EOF

docker exec qvs-postgres pg_dump \
  -U qvs -d qvs_benchmarks \
  --data-only --table=benchmark_results \
  --no-comments \
  >> "$OUT"

echo "Dumped to $OUT"
