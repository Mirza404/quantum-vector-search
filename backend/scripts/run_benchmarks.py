#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, List
import sys

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from qvs.benchmark import BenchmarkQuery, BenchmarkResult, DatabaseStorage, load_benchmark_queries
from qvs.engines.faiss_flat import FaissFlatEngine
from qvs.engines.qiskit_swaptest import QiskitSwapTestEngine
from qvs.engines.quantum_mock import QuantumMockEngine
from qvs.engines.vector_mock import VectorMockEngine
from qvs.pipeline import CLIPEmbeddingModel


@dataclass(frozen=True)
class BenchmarkSelection:
    engines: List[str]
    dimensions: List[int]
    queries: List[str]
    top_k: int = 3
    shots: int = 2048
    layers: int = 2


LIST_KEYS = {"engines", "dimensions", "queries"}
SCALAR_KEYS = {"top_k", "shots", "layers"}
CONFIG_KEYS = LIST_KEYS | SCALAR_KEYS


def _accuracy_score(target_ids: List[str], ranked_ids: List[str]) -> float:
    weights = [1.0, 0.66, 0.33]
    best_idx: int | None = None
    for target in target_ids:
        try:
            idx = ranked_ids.index(target)
        except ValueError:
            continue
        if best_idx is None or idx < best_idx:
            best_idx = idx
    if best_idx is None or best_idx >= len(weights):
        return 0.0
    return weights[best_idx]


def _prepare_vectors(matrix: np.ndarray, dimension: int) -> List[List[float]]:
    truncated = matrix[:, :dimension]
    return truncated.tolist()


def _engine_factories(seed: int | None, dimension: int) -> dict[str, Callable[[], object]]:
    return {
        "vector_mock_cosine": lambda: VectorMockEngine(),
        "quantum_mock_sampler": lambda: QuantumMockEngine(seed=seed),
        "faiss_flat_l2": lambda: FaissFlatEngine(dimension=dimension),
        "qiskit_swap_test": lambda: QiskitSwapTestEngine(),
    }



def _resolve_config_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    backend_root = Path(__file__).resolve().parent.parent
    return backend_root / candidate


def _load_selection_config(path: Path) -> BenchmarkSelection:
    if not path.exists():
        raise SystemExit(f"Benchmark config not found: {path}")
    lists: dict[str, List[str]] = {}
    scalars: dict[str, str] = {}
    current_list_key: str | None = None
    for idx, raw_line in enumerate(path.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.endswith(":"):
            # scalar: key: value
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.split("#", 1)[0].strip()
            if key not in CONFIG_KEYS:
                allowed = ", ".join(sorted(CONFIG_KEYS))
                raise SystemExit(f"Unknown key '{key}' in {path} line {idx}. Expected one of: {allowed}.")
            scalars[key] = value
            current_list_key = None
            continue
        if line.endswith(":"):
            key = line[:-1].strip()
            if key not in CONFIG_KEYS:
                allowed = ", ".join(sorted(CONFIG_KEYS))
                raise SystemExit(f"Unknown key '{key}' in {path} line {idx}. Expected one of: {allowed}.")
            lists[key] = []
            current_list_key = key
            continue
        if line.startswith("-"):
            if current_list_key is None:
                raise SystemExit(f"List item defined before a key at {path} line {idx}: {raw_line}")
            value = line[1:].split("#", 1)[0].strip()
            if not value:
                continue
            lists[current_list_key].append(value)
            continue
        raise SystemExit(f"Unsupported syntax in {path} line {idx}: {raw_line}")

    missing = [key for key in LIST_KEYS if key not in lists]
    if missing:
        raise SystemExit(f"Missing sections in {path}: {', '.join(missing)}")
    if not lists["engines"]:
        raise SystemExit(f"No engines enabled in {path}.")
    if not lists["dimensions"]:
        raise SystemExit(f"No dimensions listed in {path}.")
    if not lists["queries"]:
        raise SystemExit(f"No queries listed in {path}.")

    try:
        dimensions = [int(entry) for entry in lists["dimensions"]]
    except ValueError as exc:
        raise SystemExit(f"All dimension entries in {path} must be integers.") from exc

    def _int_scalar(key: str, default: int) -> int:
        if key not in scalars:
            return default
        try:
            return int(scalars[key])
        except ValueError:
            raise SystemExit(f"'{key}' in {path} must be an integer, got: {scalars[key]!r}")

    return BenchmarkSelection(
        engines=lists["engines"],
        dimensions=dimensions,
        queries=lists["queries"],
        top_k=_int_scalar("top_k", 3),
        shots=_int_scalar("shots", 2048),
        layers=_int_scalar("layers", 2),
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
    parser.add_argument("--dataset-dir", default="data/sample_dataset/images", help="Dataset directory")
    parser.add_argument("--ground-truth", default=None, help="Ground-truth JSON (defaults to <dataset>/ground_truth.json)")
    parser.add_argument("--config", default="config/benchmarks.yaml", help="Relative or absolute path to benchmark selection YAML")
    parser.add_argument(
        "--dimensions",
        nargs="+",
        type=int,
        default=None,
        help="Override the dimensions from the YAML config (space-separated list)",
    )
    parser.add_argument("--top-k", type=int, default=None, help="Override top_k from benchmarks.yaml")
    parser.add_argument("--shots", type=int, default=None, help="Override shots from benchmarks.yaml")
    parser.add_argument("--layers", type=int, default=None, help="Override layers from benchmarks.yaml")
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
    top_k = args.top_k if args.top_k is not None else selection.top_k
    shots = args.shots if args.shots is not None else selection.shots
    layers = args.layers if args.layers is not None else selection.layers

    dataset_dir = Path(args.dataset_dir).resolve()
    ground_truth_path = (
        Path(args.ground_truth).resolve()
        if args.ground_truth
        else (BACKEND_ROOT / "data" / "sample_dataset" / "ground_truth.json").resolve()
    )

    queries = load_benchmark_queries(ground_truth_path)
    queries = _select_queries(selection.queries, queries)

    storage = DatabaseStorage()
    stored_vectors = storage.load_image_vectors()
    if not stored_vectors:
        raise SystemExit(
            "No image vectors found in the database. "
            "Run `python3 scripts/index_dataset.py` first to encode and store image embeddings."
        )

    all_target_ids = {tid for query in queries for tid in query.target_ids}
    missing = all_target_ids - stored_vectors.keys()
    if missing:
        raise SystemExit(
            f"The following image IDs are referenced in ground_truth.json but have no stored embedding: "
            f"{', '.join(sorted(missing))}. "
            "Run `python3 scripts/index_dataset.py` to encode all images."
        )

    dataset_ids = list(stored_vectors.keys())
    dataset_matrix = np.array([stored_vectors[id_] for id_ in dataset_ids], dtype=np.float32)
    dataset_dim = dataset_matrix.shape[1]
    max_requested = max(dimensions)
    if max_requested > dataset_dim:
        raise SystemExit(
            f"Requested dimension ({max_requested}) exceeds dataset embedding dimension ({dataset_dim}). Reduce --dimensions."
        )

    clip_model = CLIPEmbeddingModel(
        model_name=args.clip_model,
        device=args.device,
        batch_size=args.batch_size,
        normalize=not args.no_normalize,
    )
    query_matrix = clip_model.encode_texts([query.text for query in queries])
    if query_matrix.shape[1] > dataset_dim:
        query_matrix = query_matrix[:, :dataset_dim]
    query_vectors = {
        query.id: query_matrix[idx].astype(np.float32).tolist() for idx, query in enumerate(queries)
    }
    engine_names = selection.engines

    for dimension in sorted(dimensions):
        engine_factories = _engine_factories(args.quantum_seed, dimension)
        missing_engines = [name for name in engine_names if name not in engine_factories]
        if missing_engines:
            raise SystemExit(
                f"Unknown engine names in {config_path}: {', '.join(missing_engines)}. "
                "Ensure the YAML file only lists available implementations."
            )
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

                search_kwargs = {"query_vector": query_vector, "top_k": top_k}
                if "quantum" in engine.name:
                    search_kwargs.update({"shots": shots, "layers": layers})

                search_start = perf_counter()
                result = engine.search(**search_kwargs)
                search_ms = (perf_counter() - search_start) * 1000
                total_ms = prep_ms + search_ms

                accuracy = _accuracy_score(query.target_ids, result.ids)
                parameters = {
                    "dimension": dimension,
                    "top_k": top_k,
                }
                if "quantum" in engine.name:
                    parameters.update({"shots": shots, "layers": layers})

                meta = result.meta or {}
                storage.append(
                    BenchmarkResult(
                        query_id=query.id,
                        engine_name=engine.name,
                        dimension=dimension,
                        target_ids=query.target_ids,
                        top_ids=result.ids,
                        accuracy=accuracy,
                        state_prep_ms=prep_ms if "quantum" in engine.name else 0.0,
                        search_ms=search_ms,
                        total_ms=total_ms,
                        parameters=parameters,
                        dataset_size=len(dataset_ids),
                        circuit_depth=meta.get("circuit_depth"),
                        num_qubits=meta.get("num_qubits"),
                    )
                )
                print(
                    f"[{engine.name}] query={query.id} dim={dimension} accuracy={accuracy:.2f} total_ms={total_ms:.2f}"
                )


if __name__ == "__main__":
    main()
