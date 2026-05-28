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
    env_path = Path(__file__).resolve().parents[2] / ".env"  # backend/.env
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
        from pgvector.psycopg import register_vector
        register_vector(self._conn)

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

    def has_record(self, key: tuple[str, str, int, int | None, int | None]) -> bool:
        query_id, engine_name, dimension, shots, layers = key
        sql = """
            SELECT 1
            FROM benchmark_results
            WHERE query_id = %s AND engine_name = %s AND dimension = %s
              AND shots = %s AND layers = %s
            LIMIT 1
        """
        with self._conn.cursor() as cursor:
            cursor.execute(sql, (query_id, engine_name, dimension,
                                 shots if shots is not None else -1,
                                 layers if layers is not None else -1))
            return cursor.fetchone() is not None

    def append(self, result: BenchmarkResult) -> None:
        sql = """
            INSERT INTO benchmark_results (
                recorded_at,
                query_id,
                engine_name,
                dimension,
                shots,
                layers,
                target_ids,
                top_ids,
                state_prep_ms,
                search_ms,
                total_ms,
                parameters,
                dataset_size,
                circuit_depth,
                num_qubits,
                oracle_calls
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_run_key DO UPDATE SET
                recorded_at   = EXCLUDED.recorded_at,
                target_ids    = EXCLUDED.target_ids,
                top_ids       = EXCLUDED.top_ids,
                state_prep_ms = EXCLUDED.state_prep_ms,
                search_ms     = EXCLUDED.search_ms,
                total_ms      = EXCLUDED.total_ms,
                parameters    = EXCLUDED.parameters,
                dataset_size  = EXCLUDED.dataset_size,
                circuit_depth = EXCLUDED.circuit_depth,
                num_qubits    = EXCLUDED.num_qubits,
                oracle_calls  = EXCLUDED.oracle_calls
        """
        payload = (
            result.timestamp,
            result.query_id,
            result.engine_name,
            result.dimension,
            result.shots if result.shots is not None else -1,
            result.layers if result.layers is not None else -1,
            self._json_wrapper(result.target_ids),
            self._json_wrapper(result.top_ids),
            result.state_prep_ms,
            result.search_ms,
            result.total_ms,
            self._json_wrapper(result.parameters),
            result.dataset_size,
            result.circuit_depth,
            result.num_qubits,
            result.oracle_calls,
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

    def load_image_vectors(self) -> dict[str, list[float]]:
        """Load all rows from image_vectors. Returns {id: vector}."""
        sql = "SELECT id, embedding FROM image_vectors"
        with self._conn.cursor() as cursor:
            cursor.execute(sql)
            return {row[0]: row[1].tolist() for row in cursor.fetchall()}

    def load_benchmark_summary(self, query_id: str | None = None) -> list[dict]:
        if query_id:
            where = "WHERE query_id = %s"
            params = (query_id,)
        else:
            where = ""
            params = ()
        sql = f"""
            SELECT
                engine_name,
                AVG(
                    CASE
                        WHEN top_ids::jsonb @> target_ids::jsonb THEN
                            1.0 / (
                                SELECT idx
                                FROM jsonb_array_elements_text(top_ids::jsonb) WITH ORDINALITY arr(val, idx)
                                WHERE val = (target_ids::jsonb ->> 0)
                                LIMIT 1
                            )
                        ELSE 0.0
                    END
                ) as avg_mrr,
                AVG(search_ms) as avg_search_ms,
                AVG(state_prep_ms) as avg_state_prep_ms,
                AVG(total_ms) as avg_total_ms,
                MAX(circuit_depth) as circuit_depth,
                MAX(num_qubits) as num_qubits,
                AVG(oracle_calls) as avg_oracle_calls,
                COUNT(*) as total_runs
            FROM benchmark_results
            {where}
            GROUP BY engine_name
            ORDER BY engine_name
        """
        with self._conn.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def load_benchmark_breakdown(self) -> list[dict]:
        """Per (engine, dimension, shots) row — does NOT collapse across configs.

        Used by the API to surface the shots-vs-MRR curve that RQ1 requires; the
        aggregated `load_benchmark_summary` view hides that breakdown.
        """
        sql = """
            SELECT
                engine_name,
                dimension,
                shots,
                AVG(
                    CASE
                        WHEN top_ids::jsonb @> target_ids::jsonb THEN
                            1.0 / (
                                SELECT idx
                                FROM jsonb_array_elements_text(top_ids::jsonb) WITH ORDINALITY arr(val, idx)
                                WHERE val = (target_ids::jsonb ->> 0)
                                LIMIT 1
                            )
                        ELSE 0.0
                    END
                ) as avg_mrr,
                AVG(search_ms) as avg_search_ms,
                AVG(state_prep_ms) as avg_state_prep_ms,
                AVG(total_ms) as avg_total_ms,
                MAX(circuit_depth) as circuit_depth,
                MAX(num_qubits) as num_qubits,
                AVG(oracle_calls) as avg_oracle_calls,
                COUNT(*) as runs
            FROM benchmark_results
            GROUP BY engine_name, dimension, shots
            ORDER BY engine_name, dimension, shots
        """
        with self._conn.cursor() as cursor:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self) -> None:
        self._conn.close()

    def __del__(self) -> None:  # pragma: no cover - defensive cleanup
        with contextlib.suppress(Exception):
            self.close()
