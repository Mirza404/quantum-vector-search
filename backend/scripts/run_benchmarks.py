#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import List

import numpy as np

from qvs.benchmark import BenchmarkResult, CsvMarkdownStorage, load_benchmark_queries
from qvs.engines.quantum_mock import QuantumMockEngine
from qvs.engines.vector_mock import VectorMockEngine
from qvs.pipeline import EmbeddingCache, MockCLIPEmbeddingGenerator
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


def _ensure_cache(cache_dir: Path) -> tuple[np.ndarray, int]:
    cache = EmbeddingCache(cache_dir)
    snapshot = cache.load()
    if not snapshot:
        raise SystemExit(f"No embedding cache found in {cache_dir}. Run scripts/build_embeddings.py first.")
    matrix = cache.load_matrix()
    if matrix is None:
        raise SystemExit(f"Embeddings file missing at {cache.embeddings_path()}")
    return matrix, snapshot.dimension


def _create_engines(seed: int | None) -> list:
    return [
        VectorMockEngine(),
        QuantumMockEngine(seed=seed),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated benchmarking harness")
    parser.add_argument("--dataset-dir", default="data/sample_dataset", help="Dataset directory")
    parser.add_argument("--cache-dir", default=None, help="Embedding cache directory (defaults to <dataset>/cache)")
    parser.add_argument("--ground-truth", default=None, help="Ground-truth JSON (defaults to <dataset>/ground_truth.json)")
    parser.add_argument("--output-dir", default="artifacts/benchmarks", help="Directory for CSV + Markdown outputs")
    parser.add_argument("--metadata", default="metadata.csv", help="Dataset metadata filename")
    parser.add_argument("--dimensions", nargs="+", type=int, default=[8], help="List of vector dimensions to test")
    parser.add_argument("--top-k", type=int, default=3, help="Number of neighbors to retrieve")
    parser.add_argument("--shots", type=int, default=2048, help="Quantum shots parameter")
    parser.add_argument("--layers", type=int, default=2, help="Quantum layers parameter")
    parser.add_argument("--seed", type=str, default="mock-clip", help="Seed for embedding generator")
    parser.add_argument("--quantum-seed", type=int, default=42, help="Seed for quantum noise rng")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir).resolve()
    cache_dir = Path(args.cache_dir) if args.cache_dir else dataset_dir / "cache"
    cache_dir = cache_dir.resolve()
    ground_truth_path = (
        Path(args.ground_truth).resolve()
        if args.ground_truth
        else (dataset_dir / "ground_truth.json").resolve()
    )

    loader = LocalCSVDataLoader(dataset_dir=dataset_dir, metadata_filename=args.metadata)
    dataset = loader.get_dataset()
    queries = load_benchmark_queries(ground_truth_path)

    matrix, cached_dim = _ensure_cache(cache_dir)
    max_requested = max(args.dimensions)
    if cached_dim < max_requested:
        raise SystemExit(
            f"Cache dimension ({cached_dim}) is smaller than requested dimension ({max_requested}). Re-run build_embeddings.py."
        )

    output_dir = Path(args.output_dir).resolve()
    storage = CsvMarkdownStorage(
        csv_path=output_dir / "results.csv",
        markdown_path=output_dir / "Report.md",
    )

    embedder = MockCLIPEmbeddingGenerator(seed=args.seed)
    dataset_ids = dataset.ids()

    for dimension in sorted(args.dimensions):
        vectors = _prepare_vectors(matrix, dimension)
        for query in queries:
            # Build query embedding and trim to current dimension
            query_full = embedder.embed(query.text, dimension=cached_dim)
            query_vector = query_full[:dimension]
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
