#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import List

import numpy as np

from qvs.benchmark import BenchmarkResult, DatabaseStorage, load_benchmark_queries
from qvs.engines.quantum_mock import QuantumMockEngine
from qvs.engines.vector_mock import VectorMockEngine
from qvs.pipeline import CLIPEmbeddingModel
from qvs.repository import LocalCSVDataLoader


def _accuracy_score(target_id: str, ranked_ids: List[str]) -> float:
    weights = [1.0, 0.66, 0.33]
    try:
        idx = ranked_ids.index(target_id)
    except ValueError:
        return 0.0
    if idx >= len(weights):
        return 0.0
    return weights[idx]


def _prepare_vectors(matrix: np.ndarray, dimension: int) -> List[List[float]]:
    truncated = matrix[:, :dimension]
    return truncated.tolist()


def _create_engines(seed: int | None) -> list:
    return [
        VectorMockEngine(),
        QuantumMockEngine(seed=seed),
    ]


def _encode_dataset_vectors(model: CLIPEmbeddingModel, image_paths: List[Path]) -> np.ndarray:
    matrix = model.encode_images(image_paths)
    return matrix.astype(np.float32, copy=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated benchmarking harness")
    parser.add_argument("--dataset-dir", default="data/sample_dataset", help="Dataset directory")
    parser.add_argument("--ground-truth", default=None, help="Ground-truth JSON (defaults to <dataset>/ground_truth.json)")
    parser.add_argument("--metadata", default="metadata.csv", help="Dataset metadata filename")
    parser.add_argument("--dimensions", nargs="+", type=int, default=[128], help="List of vector dimensions to test")
    parser.add_argument("--top-k", type=int, default=3, help="Number of neighbors to retrieve")
    parser.add_argument("--shots", type=int, default=2048, help="Quantum shots parameter")
    parser.add_argument("--layers", type=int, default=2, help="Quantum layers parameter")
    parser.add_argument("--quantum-seed", type=int, default=42, help="Seed for quantum noise rng")
    parser.add_argument("--clip-model", default="ViT-B/32", help="CLIP model name for query embeddings")
    parser.add_argument("--device", default=None, help="Torch device override passed to CLIP")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for CLIP query embedding")
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable L2 normalization for CLIP query embeddings (enabled by default)",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()
    ground_truth_path = (
        Path(args.ground_truth).resolve()
        if args.ground_truth
        else (dataset_dir / "ground_truth.json").resolve()
    )

    loader = LocalCSVDataLoader(dataset_dir=dataset_dir, metadata_filename=args.metadata)
    dataset = loader.get_dataset()
    queries = load_benchmark_queries(ground_truth_path)

    clip_model = CLIPEmbeddingModel(
        model_name=args.clip_model,
        device=args.device,
        batch_size=args.batch_size,
        normalize=not args.no_normalize,
    )
    dataset_matrix = _encode_dataset_vectors(clip_model, [record.image_path for record in dataset.records])
    dataset_dim = dataset_matrix.shape[1]
    max_requested = max(args.dimensions)
    if max_requested > dataset_dim:
        raise SystemExit(
            f"Requested dimension ({max_requested}) exceeds dataset embedding dimension ({dataset_dim}). Reduce --dimensions."
        )
    dataset_ids = dataset.ids()
    query_matrix = clip_model.encode_texts([query.text for query in queries])
    if query_matrix.shape[1] > dataset_dim:
        query_matrix = query_matrix[:, :dataset_dim]
    query_vectors = {
        query.id: query_matrix[idx].astype(np.float32).tolist() for idx, query in enumerate(queries)
    }
    storage = DatabaseStorage()

    for dimension in sorted(args.dimensions):
        vectors = _prepare_vectors(dataset_matrix, dimension)
        for query in queries:
            # Build query embedding and trim to current dimension
            full_query_vector = query_vectors[query.id]
            query_vector = full_query_vector[:dimension]
            for engine in _create_engines(args.quantum_seed):
                key = (query.id, engine.name, dimension)
                if storage.has_record(key):
                    continue

                prep_start = perf_counter()
                engine.build_index(vectors=vectors, ids=dataset_ids)
                prep_ms = (perf_counter() - prep_start) * 1000

                search_kwargs = {"query_vector": query_vector, "top_k": args.top_k}
                if "quantum" in engine.name:
                    search_kwargs.update({"shots": args.shots, "layers": args.layers})

                search_start = perf_counter()
                result = engine.search(**search_kwargs)
                search_ms = (perf_counter() - search_start) * 1000
                total_ms = prep_ms + search_ms

                accuracy = _accuracy_score(query.target_id, result.ids)
                parameters = {
                    "dimension": dimension,
                    "top_k": args.top_k,
                }
                if "quantum" in engine.name:
                    parameters.update({"shots": args.shots, "layers": args.layers})

                storage.append(
                    BenchmarkResult(
                        query_id=query.id,
                        engine_name=engine.name,
                        dimension=dimension,
                        target_id=query.target_id,
                        top_ids=result.ids,
                        accuracy=accuracy,
                        state_prep_ms=prep_ms if "quantum" in engine.name else 0.0,
                        search_ms=search_ms,
                        total_ms=total_ms,
                        parameters=parameters,
                    )
                )
                print(
                    f"[{engine.name}] query={query.id} dim={dimension} accuracy={accuracy:.2f} total_ms={total_ms:.2f}"
                )


if __name__ == "__main__":
    main()
