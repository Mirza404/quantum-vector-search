from __future__ import annotations

import contextlib
import os
from pathlib import Path

from .base import BaseBenchmarkStorage
from .models import BenchmarkResult


def _load_env_file(path: Path) -> None:
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def _bootstrap_env() -> None:
    base_path = Path(__file__).resolve()
    candidates = []
    for depth in (3, 4):  # backend/, then repo root fallback
        try:
            candidate = base_path.parents[depth] / ".env"
        except IndexError:
            continue
        if candidate.exists():
            candidates.append(candidate)
    for path in candidates:
        _load_env_file(path)


_bootstrap_env()


class DatabaseStorage(BaseBenchmarkStorage):
    """Persist benchmark results inside PostgreSQL."""

    def __init__(self, *, dsn: str | None = None, env_var: str = "QVS_BENCHMARK_DSN") -> None:
        self._dsn = dsn or os.getenv(env_var)
        if not self._dsn:
            raise RuntimeError(
                f"DatabaseStorage requires a PostgreSQL DSN. Set the {env_var} environment variable."
            )
        psycopg_mod, json_wrapper = self._load_psycopg()
        self._json_wrapper = json_wrapper
        self._conn = psycopg_mod.connect(self._dsn)
        self._conn.autocommit = True

    @staticmethod
    def _load_psycopg():
        try:
            import psycopg  # type: ignore
            from psycopg.types import json as psycopg_json  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "DatabaseStorage requires the 'psycopg' package. Install it with `pip install psycopg[binary]`."
            ) from exc
        return psycopg, psycopg_json.Json

    def has_record(self, key: tuple[str, str, int]) -> bool:
        query_id, engine_name, dimension = key
        sql = """
            SELECT 1
            FROM benchmark_results
            WHERE query_id = %s AND engine_name = %s AND dimension = %s
            LIMIT 1
        """
        with self._conn.cursor() as cursor:
            cursor.execute(sql, (query_id, engine_name, dimension))
            return cursor.fetchone() is not None

    def append(self, result: BenchmarkResult) -> None:
        sql = """
            INSERT INTO benchmark_results (
                recorded_at,
                query_id,
                engine_name,
                dimension,
                target_id,
                top_ids,
                accuracy,
                state_prep_ms,
                search_ms,
                total_ms,
                parameters
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (query_id, engine_name, dimension) DO NOTHING
        """
        payload = (
            result.timestamp,
            result.query_id,
            result.engine_name,
            result.dimension,
            result.target_id,
            self._json_wrapper(result.top_ids),
            result.accuracy,
            result.state_prep_ms,
            result.search_ms,
            result.total_ms,
            self._json_wrapper(result.parameters),
        )
        with self._conn.cursor() as cursor:
            cursor.execute(sql, payload)

    def close(self) -> None:
        self._conn.close()

    def __del__(self) -> None:  # pragma: no cover - defensive cleanup
        with contextlib.suppress(Exception):
            self.close()
