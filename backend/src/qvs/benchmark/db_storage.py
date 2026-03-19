from __future__ import annotations

import contextlib
import os
from pathlib import Path
from typing import Iterable

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
    env_path = Path(__file__).resolve().parents[3] / ".env"  # backend/.env
    if env_path.exists():
        _load_env_file(env_path)


_bootstrap_env()


class DatabaseStorage(BaseBenchmarkStorage):
    """Persist benchmark results inside PostgreSQL."""

    def __init__(self, *, dsn: str | None = None) -> None:
        psycopg_mod, json_wrapper = self._load_psycopg()
        self._json_wrapper = json_wrapper
        if dsn:
            self._conn = psycopg_mod.connect(dsn)
        else:
            self._conn = psycopg_mod.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "6432")),
                dbname=os.getenv("DB_NAME", "qvs_benchmarks"),
                user=os.getenv("DB_USER", "qvs"),
                password=os.getenv("DB_PASSWORD", "qvs"),
            )
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
                target_ids,
                top_ids,
                accuracy,
                state_prep_ms,
                search_ms,
                total_ms,
                parameters,
                dataset_size,
                circuit_depth,
                num_qubits
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (query_id, engine_name, dimension) DO NOTHING
        """
        payload = (
            result.timestamp,
            result.query_id,
            result.engine_name,
            result.dimension,
            self._json_wrapper(result.target_ids),
            self._json_wrapper(result.top_ids),
            result.accuracy,
            result.state_prep_ms,
            result.search_ms,
            result.total_ms,
            self._json_wrapper(result.parameters),
            result.dataset_size,
            result.circuit_depth,
            result.num_qubits,
        )
        with self._conn.cursor() as cursor:
            cursor.execute(sql, payload)

    def upsert_image_vectors(self, rows: Iterable[tuple[str, list[float]]]) -> int:
        """Upsert (id, embedding) pairs into image_vectors. Returns the number of rows written."""
        sql = (
            "INSERT INTO image_vectors (id, embedding, recorded_at) "
            "VALUES (%s, %s::vector, NOW()) "
            "ON CONFLICT (id) DO UPDATE "
            "SET embedding = EXCLUDED.embedding, recorded_at = EXCLUDED.recorded_at"
        )
        formatted = [
            (image_id, "[" + ", ".join(f"{v:.8f}" for v in vector) + "]")
            for image_id, vector in rows
        ]
        with self._conn.cursor() as cursor:
            cursor.executemany(sql, formatted)
        return len(formatted)

    def close(self) -> None:
        self._conn.close()

    def __del__(self) -> None:  # pragma: no cover - defensive cleanup
        with contextlib.suppress(Exception):
            self.close()
