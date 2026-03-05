#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Dict

import numpy as np

from qvs.pipeline import EmbeddingCache, EmbeddingCacheEntry, MockCLIPEmbeddingGenerator
from qvs.repository import LocalCSVDataLoader


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Incremental embedding builder")
    parser.add_argument("--dataset-dir", default="data/sample_dataset", help="Dataset directory")
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Cache directory (defaults to <dataset>/cache)",
    )
    parser.add_argument("--metadata", default="metadata.csv", help="Metadata filename")
    parser.add_argument("--dimension", type=int, default=16, help="Embedding dimension")
    parser.add_argument("--seed", default="mock-clip", help="Deterministic seed for the mock embedder")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore any existing cache and rebuild every vector",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()
    cache_dir = Path(args.cache_dir) if args.cache_dir else dataset_dir / "cache"
    cache_dir = cache_dir.resolve()

    loader = LocalCSVDataLoader(dataset_dir=dataset_dir, metadata_filename=args.metadata)
    dataset = loader.get_dataset()

    cache = EmbeddingCache(cache_dir)
    snapshot = None if args.force else cache.load()
    existing_matrix = cache.load_matrix() if snapshot else None
    generator = MockCLIPEmbeddingGenerator(seed=args.seed)

    id_to_vector: Dict[str, np.ndarray] = {}
    if snapshot and existing_matrix is not None and snapshot.dimension == args.dimension:
        for _id, entry in snapshot.entries.items():
            if 0 <= entry.index < len(existing_matrix):
                id_to_vector[_id] = existing_matrix[entry.index]

    rows: list[np.ndarray] = []
    manifest: Dict[str, EmbeddingCacheEntry] = {}
    reused = 0
    recomputed = 0

    for idx, record in enumerate(dataset.records):
        text_hash = _hash_text(record.text)
        vector: np.ndarray | None = None
        entry = snapshot.entries.get(record.id) if snapshot else None
        if (
            entry
            and entry.text_hash == text_hash
            and record.id in id_to_vector
            and snapshot.dimension == args.dimension
        ):
            vector = id_to_vector[record.id]
            reused += 1
        else:
            vector = np.asarray(generator.embed(record.text, dimension=args.dimension), dtype=float)
            recomputed += 1
        rows.append(vector)
        manifest[record.id] = EmbeddingCacheEntry(text_hash=text_hash, index=idx)

    matrix = np.vstack(rows)
    cache.save(dimension=args.dimension, entries=manifest, matrix=matrix)
    print(
        "Cached {} embeddings ({} reused / {} recomputed) -> {}".format(
            len(rows), reused, recomputed, cache.embeddings_path()
        )
    )


if __name__ == "__main__":
    main()
