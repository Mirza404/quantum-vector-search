#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

from qvs.pipeline import CLIPEmbeddingModel, EmbeddingCache, EmbeddingCacheEntry
from qvs.repository import LocalCSVDataLoader


def _hash_file(path: Path, *, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _record_hash(text: str, image_path: Path) -> str:
    if not image_path.exists():
        raise FileNotFoundError(f"image not found: {image_path}")
    digest = hashlib.sha256()
    digest.update(text.strip().encode("utf-8"))
    digest.update(b"\0")
    digest.update(_hash_file(image_path).encode("utf-8"))
    return digest.hexdigest()


def _reuse_vectors(
    snapshot,
    matrix: np.ndarray | None,
    target_dimension: int,
) -> Dict[str, np.ndarray]:
    if not snapshot or matrix is None or snapshot.dimension != target_dimension:
        return {}
    reused: Dict[str, np.ndarray] = {}
    for _id, entry in snapshot.entries.items():
        if 0 <= entry.index < len(matrix):
            reused[_id] = matrix[entry.index]
    return reused


def _prepare_new_embeddings(
    clip_model: CLIPEmbeddingModel,
    records: Sequence,
    pending_indices: List[int],
    target_dimension: int,
) -> List[np.ndarray]:
    if not pending_indices:
        return []
    paths = [records[idx].image_path for idx in pending_indices]
    computed = clip_model.encode_images(paths)
    if target_dimension < computed.shape[1]:
        computed = computed[:, :target_dimension]
    return [np.asarray(vector, dtype=np.float32) for vector in computed]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build (or refresh) CLIP embeddings for the dataset")
    parser.add_argument("--dataset-dir", default="data/sample_dataset", help="Dataset directory")
    parser.add_argument("--cache-dir", default=None, help="Cache directory (defaults to <dataset>/cache)")
    parser.add_argument("--metadata", default="metadata.csv", help="Metadata filename")
    parser.add_argument(
        "--dimension",
        type=int,
        default=None,
        help="Target embedding dimension (defaults to the CLIP output size)",
    )
    parser.add_argument("--clip-model", default="ViT-B/32", help="CLIP model name (passed to clip.load)")
    parser.add_argument("--device", default=None, help="Torch device override (cpu, cuda, mps, etc.)")
    parser.add_argument("--batch-size", type=int, default=16, help="Mini-batch size for CLIP inference")
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable L2 normalization of the embeddings (enabled by default)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore any existing cache snapshot and rebuild every vector",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else (dataset_dir / "cache").resolve()

    loader = LocalCSVDataLoader(dataset_dir=dataset_dir, metadata_filename=args.metadata)
    dataset = loader.get_dataset()
    if not dataset.records:
        raise SystemExit(f"No rows found in {dataset_dir}")

    clip_model = CLIPEmbeddingModel(
        model_name=args.clip_model,
        device=args.device,
        batch_size=args.batch_size,
        normalize=not args.no_normalize,
    )
    clip_dim = clip_model.embedding_dimension
    target_dimension = args.dimension or clip_dim
    if target_dimension > clip_dim:
        raise SystemExit(f"Requested dimension {target_dimension} exceeds CLIP output {clip_dim}")

    cache = EmbeddingCache(cache_dir)
    snapshot = None if args.force else cache.load()
    existing_matrix = cache.load_matrix() if snapshot else None
    id_to_vector = _reuse_vectors(snapshot, existing_matrix, target_dimension)

    rows: List[np.ndarray | None] = [None] * len(dataset.records)
    manifest: Dict[str, EmbeddingCacheEntry] = {}
    pending_indices: List[int] = []
    reused = 0

    for idx, record in enumerate(dataset.records):
        content_hash = _record_hash(record.text, record.image_path)
        vector = None
        entry = snapshot.entries.get(record.id) if snapshot else None
        if entry and entry.content_hash == content_hash and record.id in id_to_vector:
            vector = np.asarray(id_to_vector[record.id], dtype=np.float32)
            reused += 1
        else:
            pending_indices.append(idx)
        rows[idx] = vector
        manifest[record.id] = EmbeddingCacheEntry(content_hash=content_hash, index=idx)

    new_vectors = _prepare_new_embeddings(clip_model, dataset.records, pending_indices, target_dimension)
    recomputed = len(new_vectors)
    for idx, vector in zip(pending_indices, new_vectors, strict=False):
        rows[idx] = vector

    if any(row is None for row in rows):
        raise RuntimeError("unexpected None row after embedding pass")

    matrix = np.vstack(rows).astype(np.float32, copy=False)
    cache.save(dimension=target_dimension, entries=manifest, matrix=matrix)
    print(
        f"Cached {len(rows)} embeddings ({reused} reused / {recomputed} recomputed) -> {cache.embeddings_path()}"
    )


if __name__ == "__main__":
    main()
