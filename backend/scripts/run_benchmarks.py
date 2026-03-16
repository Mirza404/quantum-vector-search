#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, List

import numpy as np

from qvs.benchmark import BenchmarkQuery, BenchmarkResult, DatabaseStorage, load_benchmark_queries
from qvs.engines.quantum_mock import QuantumMockEngine
from qvs.engines.vector_mock import VectorMockEngine
from qvs.pipeline import CLIPEmbeddingModel
from qvs.repository import LocalCSVDataLoader


@dataclass(frozen=True)
class BenchmarkSelection:
    engines: List[str]
    dimensions: List[int]
    queries: List[str]


CONFIG_KEYS = {"engines", "dimensions", "queries"}


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


def _engine_factories(seed: int | None) -> dict[str, Callable[[], object]]:
    return {
        "vector_mock_cosine": lambda: VectorMockEngine(),
        "quantum_mock_sampler": lambda: QuantumMockEngine(seed=seed),
    }


def _encode_dataset_vectors(model: CLIPEmbeddingModel, image_paths: List[Path]) -> np.ndarray:
    matrix = model.encode_images(image_paths)
    return matrix.astype(np.float32, copy=False)


def _resolve_config_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    backend_root = Path(__file__).resolve().parent.parent
    return backend_root / candidate


def _load_selection_config(path: Path) -> BenchmarkSelection:
    if not path.exists():
        raise SystemExit(f"Benchmark config not found: {path}")
    config: dict[str, List[str]] = {}
    current_key: str | None = None
    for idx, raw_line in enumerate(path.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":"):
            key = line[:-1].strip()
            if key not in CONFIG_KEYS:
                allowed = ", ".join(sorted(CONFIG_KEYS))
                raise SystemExit(f"Unknown key '{key}' in {path} line {idx}. Expected one of: {allowed}.")
            config[key] = []
            current_key = key
            continue
        if line.startswith("-"):
            if current_key is None:
                raise SystemExit(f"List item defined before a key at {path} line {idx}: {raw_line}")
            value = line[1:].split("#", 1)[0].strip()
            if not value:
                continue
            config[current_key].append(value)
            continue
        raise SystemExit(f"Unsupported syntax in {path} line {idx}: {raw_line}")

    missing = [key for key in CONFIG_KEYS if key not in config]
    if missing:
        raise SystemExit(f"Missing sections in {path}: {', '.join(missing)}")
    if not config["engines"]:
        raise SystemExit(f"No engines enabled in {path}.")
    if not config["dimensions"]:
        raise SystemExit(f"No dimensions listed in {path}.")
    if not config["queries"]:
        raise SystemExit(f"No queries listed in {path}.")

    try:
        dimensions = [int(entry) for entry in config["dimensions"]]
    except ValueError as exc:
        raise SystemExit(f"All dimension entries in {path} must be integers.") from exc

    return BenchmarkSelection(
        engines=config["engines"],
        dimensions=dimensions,
        queries=config["queries"],
    )


def _select_queries(requested_ids: List[str], available_queries: List[BenchmarkQuery]) -> List[BenchmarkQuery]:
    if not requested_ids:
        raise SystemExit("No query ids specified in the benchmark config.")
    lookup = {query.id: query for query in available_queries}
    missing = [query_id for query_id in requested_ids if query_id not in lookup]
    if missing:
        raise SystemExit(f"Unknown query ids in benchmark config: {', '.join(missing)}")
    return [lookup[query_id] for query_id in requested_ids]


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated benchmarking harness")
    parser.add_argument("--dataset-dir", default="data/sample_dataset", help="Dataset directory")
    parser.add_argument("--ground-truth", default=None, help="Ground-truth JSON (defaults to <dataset>/ground_truth.json)")
    parser.add_argument("--metadata", default="metadata.csv", help="Dataset metadata filename")
    parser.add_argument("--config", default="config/benchmarks.yaml", help="Relative or absolute path to benchmark selection YAML")
    parser.add_argument(
        "--dimensions",
        nargs="+",
        type=int,
        default=None,
        help="Override the dimensions from the YAML config (space-separated list)",
    )
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
    config_path = _resolve_config_path(args.config)
    selection = _load_selection_config(config_path)
    dimensions = args.dimensions or selection.dimensions

    dataset_dir = Path(args.dataset_dir).resolve()
    ground_truth_path = (
        Path(args.ground_truth).resolve()
        if args.ground_truth
        else (dataset_dir / "ground_truth.json").resolve()
    )

    loader = LocalCSVDataLoader(dataset_dir=dataset_dir, metadata_filename=args.metadata)
    dataset = loader.get_dataset()
    queries = load_benchmark_queries(ground_truth_path)
    queries = _select_queries(selection.queries, queries)

    clip_model = CLIPEmbeddingModel(
        model_name=args.clip_model,
        device=args.device,
        batch_size=args.batch_size,
        normalize=not args.no_normalize,
    )
    dataset_matrix = _encode_dataset_vectors(clip_model, [record.image_path for record in dataset.records])
    dataset_dim = dataset_matrix.shape[1]
    max_requested = max(dimensions)
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
    engine_factories = _engine_factories(args.quantum_seed)
    missing_engines = [name for name in selection.engines if name not in engine_factories]
    if missing_engines:
        raise SystemExit(
            f"Unknown engine names in {config_path}: {', '.join(missing_engines)}. "
            "Ensure the YAML file only lists available implementations."
        )
    engine_names = selection.engines

    for dimension in sorted(dimensions):
        vectors = _prepare_vectors(dataset_matrix, dimension)
        for query in queries:
            # Build query embedding and trim to current dimension
            full_query_vector = query_vectors[query.id]
            query_vector = full_query_vector[:dimension]
            for engine_name in engine_names:
                engine = engine_factories[engine_name]()
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
