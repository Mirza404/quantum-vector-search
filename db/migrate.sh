#!/usr/bin/env bash
# Usage:
#   bash db/migrate.sh          # apply all pending up migrations
#   bash db/migrate.sh up
#   bash db/migrate.sh down [N] # roll back all migrations above N (default: roll back all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$SCRIPT_DIR/.env" ] && { set -a; source "$SCRIPT_DIR/.env"; set +a; }

DB_CONTAINER="${DB_CONTAINER:-qvs-postgres}"
DB_USER="${DB_USER:-qvs}"
DB_NAME="${DB_NAME:-qvs_benchmarks}"
UP_DIR="$SCRIPT_DIR/migrations/up"
DOWN_DIR="$SCRIPT_DIR/migrations/down"

COMMAND="${1:-up}"

psql_exec() {
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" "$@"
}

bootstrap() {
    psql_exec -v ON_ERROR_STOP=1 -c "
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename   TEXT        PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    "
}

cmd_up() {
    bootstrap
    while IFS= read -r file <&3; do
        filename="$(basename "$file")"
        applied=$(psql_exec -t -A -c \
            "SELECT COUNT(*) FROM schema_migrations WHERE filename = '$filename';")
        if [ "$applied" = "0" ]; then
            echo "-> up    $filename"
            psql_exec -v ON_ERROR_STOP=1 < "$file"
            psql_exec -c "INSERT INTO schema_migrations (filename) VALUES ('$filename');"
            echo "  done"
        else
            echo "  skip  $filename"
        fi
    done 3< <(find "$UP_DIR" -maxdepth 1 -name "*.sql" | sort -V)
    echo "Up complete."
}

cmd_down() {
    local target="${1:-0}"
    bootstrap
    # Iterate in reverse order, roll back anything above the target number.
    while IFS= read -r file <&3; do
        filename="$(basename "$file")"
        number=$(echo "$filename" | grep -oP '^\d+')
        if [ "$number" -gt "$target" ]; then
            applied=$(psql_exec -t -A -c \
                "SELECT COUNT(*) FROM schema_migrations WHERE filename = '$filename';")
            if [ "$applied" != "0" ]; then
                down_file="$DOWN_DIR/$filename"
                if [ ! -f "$down_file" ]; then
                    echo "ERROR: no down migration for $filename" >&2; exit 1
                fi
                echo "<- down  $filename"
                psql_exec -v ON_ERROR_STOP=1 < "$down_file"
                psql_exec -c "DELETE FROM schema_migrations WHERE filename = '$filename';"
                echo "  done"
            fi
        fi
    done 3< <(find "$UP_DIR" -maxdepth 1 -name "*.sql" | sort -Vr)
    echo "Down complete."
}

case "$COMMAND" in
    up)   cmd_up ;;
    down) cmd_down "${2:-0}" ;;
    *)    echo "Usage: migrate.sh [up|down [N]]" >&2; exit 1 ;;
esac
