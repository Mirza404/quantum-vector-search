#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
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
from qvs.engines.brute_force_cosine import BruteForceCosineEngine
from qvs.pipeline import CLIPEmbeddingModel


@dataclass(frozen=True)
class BenchmarkSelection:
    classical_engines: List[str]
    quantum_engines: List[str]
    dimensions: List[int]
    queries: List[str]
    top_k_values: List[int] = field(default_factory=lambda: [3])
    shots_values: List[int] = field(default_factory=lambda: [2048])
    layers_values: List[int] = field(default_factory=lambda: [2])

    @property
    def engines(self) -> List[str]:
        return self.classical_engines + self.quantum_engines


LIST_KEYS = {"classical_engines", "quantum_engines", "dimensions", "queries", "top_k_values", "shots_values", "layers_values"}
SCALAR_KEYS: set[str] = set()
CONFIG_KEYS = LIST_KEYS | SCALAR_KEYS


def _recall_at_k(target_ids: List[str], ranked_ids: List[str]) -> float:
    if not target_ids:
        return 0.0
    return sum(1 for t in target_ids if t in ranked_ids) / len(target_ids)


def _mrr(target_ids: List[str], ranked_ids: List[str]) -> float:
    target_set = set(target_ids)
    for rank, item in enumerate(ranked_ids, start=1):
        if item in target_set:
            return 1.0 / rank
    return 0.0


def _prepare_vectors(matrix: np.ndarray, dimension: int) -> List[List[float]]:
    truncated = matrix[:, :dimension]
    return truncated.tolist()


def _engine_factories(seed: int | None, dimension: int) -> dict[str, Callable[[], object]]:
    return {
        "brute_force_cosine": lambda: BruteForceCosineEngine(),
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
    if not lists["classical_engines"] and not lists["quantum_engines"]:
        raise SystemExit(f"No engines enabled in {path}.")
    if not lists["dimensions"]:
        raise SystemExit(f"No dimensions listed in {path}.")
    if not lists["queries"]:
        raise SystemExit(f"No queries listed in {path}.")

    def _parse_int_list(key: str) -> List[int]:
        try:
            values = [int(entry) for entry in lists[key]]
        except ValueError as exc:
            raise SystemExit(f"All {key} entries in {path} must be integers.") from exc
        if not values:
            raise SystemExit(f"No {key} listed in {path}.")
        return values

    return BenchmarkSelection(
        classical_engines=lists["classical_engines"],
        quantum_engines=lists["quantum_engines"],
        dimensions=_parse_int_list("dimensions"),
        queries=lists["queries"],
        top_k_values=_parse_int_list("top_k_values"),
        shots_values=_parse_int_list("shots_values"),
        layers_values=_parse_int_list("layers_values"),
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
    parser.add_argument("--ground-truth", default=None, help="Ground-truth JSONC (defaults to <dataset>/ground_truth.jsonc)")
    parser.add_argument("--config", default="config/benchmarks.yaml", help="Relative or absolute path to benchmark selection YAML")
    parser.add_argument(
        "--dimensions",
        nargs="+",
        type=int,
        default=None,
        help="Override the dimensions from the YAML config (space-separated list)",
    )
    parser.add_argument("--top-k-values", nargs="+", type=int, default=None, help="Override top_k_values from benchmarks.yaml (space-separated list)")
    parser.add_argument("--shots-values", nargs="+", type=int, default=None, help="Override shots_values from benchmarks.yaml (space-separated list)")
    parser.add_argument("--layers-values", nargs="+", type=int, default=None, help="Override layers_values from benchmarks.yaml (space-separated list)")
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
    top_k_values = args.top_k_values or selection.top_k_values
    shots_values = args.shots_values or selection.shots_values
    layers_values = args.layers_values or selection.layers_values

    dataset_dir = Path(args.dataset_dir).resolve()
    ground_truth_path = (
        Path(args.ground_truth).resolve()
        if args.ground_truth
        else (BACKEND_ROOT / "data" / "sample_dataset" / "ground_truth.jsonc").resolve()
    )

    queries = load_benchmark_queries(ground_truth_path)
    queries = _select_queries(selection.queries, queries)

    max_targets = max(len(q.target_ids) for q in queries)
    invalid_top_k = [k for k in top_k_values if k < max_targets]
    if invalid_top_k:
        raise SystemExit(
            f"top_k_values {invalid_top_k} are less than the maximum number of targets in any query ({max_targets}). "
            f"All top_k_values must be >= {max_targets} — update top_k_values in benchmarks.yaml."
        )

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
            f"The following image IDs are referenced in ground_truth.jsonc but have no stored embedding: "
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
    quantum_engine_names = set(selection.quantum_engines)

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
            full_query_vector = query_vectors[query.id]
            query_vector = full_query_vector[:dimension]
            for engine_name in engine_names:
                engine = engine_factories[engine_name]()
                prep_start = perf_counter()
                engine.build_index(vectors=vectors, ids=dataset_ids)
                prep_ms = (perf_counter() - prep_start) * 1000

                is_quantum = engine.name in quantum_engine_names
                shot_iter = shots_values if is_quantum else [None]
                layer_iter = layers_values if is_quantum else [None]

                for shots in shot_iter:
                    for layers in layer_iter:
                        search_kwargs: dict = {"query_vector": query_vector, "top_k": len(dataset_ids)}
                        if is_quantum:
                            search_kwargs.update({"shots": shots, "layers": layers})

                        search_start = perf_counter()
                        result = engine.search(**search_kwargs)
                        search_ms = (perf_counter() - search_start) * 1000
                        total_ms = prep_ms + search_ms

                        meta = result.meta or {}
                        for top_k in top_k_values:
                            eval_ids = result.ids[:top_k]
                            recall = _recall_at_k(query.target_ids, eval_ids)
                            mrr = _mrr(query.target_ids, eval_ids)
                            parameters: dict = {"dimension": dimension, "top_k": top_k}
                            if is_quantum:
                                parameters.update({"shots": shots, "layers": layers})

                            storage.append(
                                BenchmarkResult(
                                    query_id=query.id,
                                    engine_name=engine.name,
                                    dimension=dimension,
                                    target_ids=query.target_ids,
                                    top_ids=eval_ids,
                                    recall_at_k=recall,
                                    mrr=mrr,
                                    state_prep_ms=prep_ms if is_quantum else 0.0,
                                    search_ms=search_ms,
                                    total_ms=total_ms,
                                    top_k=top_k,
                                    shots=shots,
                                    layers=layers,
                                    parameters=parameters,
                                    dataset_size=len(dataset_ids),
                                    circuit_depth=meta.get("circuit_depth"),
                                    num_qubits=meta.get("num_qubits"),
                                )
                            )
                            print(
                                f"[{engine.name}] query={query.id} dim={dimension} "
                                f"top_k={top_k} shots={shots} layers={layers} "
                                f"recall={recall:.2f} mrr={mrr:.3f} "
                                f"total_ms={total_ms:.2f}"
                            )


if __name__ == "__main__":
    main()
