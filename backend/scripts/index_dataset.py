#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Iterable, Iterator, Sequence

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from qvs.pipeline import CLIPEmbeddingModel
from qvs.repository import LocalCSVDataLoader

DEFAULT_DATASET_DIR = BACKEND_ROOT / "data" / "sample_dataset"
DEFAULT_METADATA_FILENAME = "metadata.csv"
DEFAULT_DSN_ENV = "QVS_BENCHMARK_DSN"
DB_BATCH_SIZE = 200


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
    candidates = [BACKEND_ROOT / ".env", BACKEND_ROOT.parent / ".env"]
    for path in candidates:
        if path.exists():
            _load_env_file(path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Encode dataset images with CLIP and store them in Postgres")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR, help="Path to dataset directory")
    parser.add_argument(
        "--metadata",
        default=DEFAULT_METADATA_FILENAME,
        help="Metadata CSV filename inside the dataset directory",
    )
    parser.add_argument("--dsn", default=None, help="PostgreSQL DSN. Overrides env var if set")
    parser.add_argument("--dsn-env", default=DEFAULT_DSN_ENV, help="Environment variable fallback for the DSN")
    parser.add_argument("--clip-model", default="ViT-B/32", help="CLIP model name")
    parser.add_argument("--device", default=None, help="Torch device for CLIP")
    parser.add_argument("--batch-size", type=int, default=32, help="CLIP batch size for image encoding")
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable L2 normalization before persisting embeddings",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only index the first N records for debugging")
    parser.add_argument(
        "--db-batch-size",
        type=int,
        default=DB_BATCH_SIZE,
        help="How many rows to upsert per transaction",
    )
    return parser.parse_args()


def _resolve_dataset_dir(path: Path) -> Path:
    if path.is_absolute():
        return path
    return (BACKEND_ROOT / path).resolve()


def _resolve_dsn(explicit: str | None, env_var: str) -> str:
    if explicit:
        return explicit
    dsn = os.getenv(env_var)
    if dsn:
        return dsn
    raise SystemExit(f"Database DSN not provided. Pass --dsn or set the {env_var} environment variable.")


def _vector_literal(vector: Sequence[float]) -> str:
    components = ", ".join(f"{float(value):.8f}" for value in vector)
    return f"[{components}]"


def _chunked(rows: Iterable[tuple[str, str]], batch_size: int) -> Iterator[list[tuple[str, str]]]:
    batch: list[tuple[str, str]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def _yield_rows(records, matrix: np.ndarray) -> Iterator[tuple[str, str]]:
    if matrix.shape[0] != len(records):
        raise RuntimeError("Embedding count does not match dataset size")
    for record, vector in zip(records, matrix, strict=True):
        yield record.id, _vector_literal(vector.tolist())


def _upsert_embeddings(conn, records, matrix: np.ndarray, batch_size: int) -> int:
    import psycopg

    sql = (
        "INSERT INTO image_vectors (id, embedding, recorded_at) "
        "VALUES (%s, %s::vector, NOW()) "
        "ON CONFLICT (id) DO UPDATE SET embedding = EXCLUDED.embedding, recorded_at = EXCLUDED.recorded_at"
    )
    total = 0
    for chunk in _chunked(_yield_rows(records, matrix), max(1, batch_size)):
        with conn.cursor() as cursor:
            cursor.executemany(sql, chunk)
        total += len(chunk)
    return total


def main() -> None:
    _bootstrap_env()
    args = _parse_args()
    dataset_dir = _resolve_dataset_dir(args.dataset_dir)
    loader = LocalCSVDataLoader(dataset_dir=dataset_dir, metadata_filename=args.metadata)
    dataset = loader.get_dataset()
    records = list(dataset.records)
    if args.limit is not None:
        records = records[: args.limit]
    if not records:
        raise SystemExit("Dataset is empty; nothing to index.")

    clip_model = CLIPEmbeddingModel(
        model_name=args.clip_model,
        device=args.device,
        batch_size=args.batch_size,
        normalize=not args.no_normalize,
    )
    image_paths = [record.image_path for record in records]
    print(f"Encoding {len(image_paths)} images with {args.clip_model}...")
    matrix = clip_model.encode_images(image_paths, normalize=not args.no_normalize)
    matrix = matrix.astype(np.float32, copy=False)
    print(f"Embeddings dimension: {matrix.shape[1]}")

    dsn = _resolve_dsn(args.dsn, args.dsn_env)
    import psycopg

    with psycopg.connect(dsn) as conn:
        conn.autocommit = True
        total = _upsert_embeddings(conn, records, matrix, args.db_batch_size)
    print(f"Upserted {total} embeddings into image_vectors.")


if __name__ == "__main__":
    main()
