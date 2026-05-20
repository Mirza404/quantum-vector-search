#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Callable, List
import sys

import numpy as np
from qiskit_aer import AerSimulator

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from benchmark import BenchmarkResult, DatabaseStorage, load_benchmark_queries  # noqa: E402
from engines.faiss_flat import FaissFlatEngine  # noqa: E402
from engines.faiss_hnsw import FaissHnswEngine  # noqa: E402
from engines.hybrid_hnsw_swaptest import HybridHnswSwapTestEngine  # noqa: E402
from engines.ibm_backend import load_ibm_backend_from_env  # noqa: E402
from engines.qiskit_grover import QiskitGroverEngine  # noqa: E402
from engines.qiskit_grover_quantum_prep import QiskitGroverQuantumPrepEngine  # noqa: E402
from engines.qiskit_swaptest import QiskitSwapTestEngine  # noqa: E402
from engines.brute_force_cosine import BruteForceCosineEngine  # noqa: E402
from pipeline import CLIPEmbeddingModel  # noqa: E402



@dataclass(frozen=True)
class BenchmarkSelection:
    classical_engines: List[str]
    quantum_engines: List[str]
    dimensions: List[int]
    shots_values: List[int] = field(default_factory=lambda: [2048])
    layers_values: List[int] = field(default_factory=lambda: [2])
    top_k: int = 10

    @property
    def engines(self) -> List[str]:
        return self.classical_engines + self.quantum_engines


LIST_KEYS = {"classical_engines", "quantum_engines", "dimensions", "shots_values", "layers_values"}
SCALAR_KEYS: set[str] = {"top_k"}
CONFIG_KEYS = LIST_KEYS | SCALAR_KEYS


def _mrr(target_ids: List[str], ranked_ids: List[str]) -> float:
    target_set = set(target_ids)
    for rank, item in enumerate(ranked_ids, start=1):
        if item in target_set:
            return 1.0 / rank
    return 0.0


def _prepare_vectors(matrix: np.ndarray, dimension: int) -> List[List[float]]:
    truncated = matrix[:, :dimension]
    return truncated.tolist()


def _oracle_calls(engine_name: str, dataset_size: int) -> int | None:
    """Derive oracle/comparison count from engine type and dataset size.

    Exact classical engines: N comparisons (linear scan).
    HNSW:                    ceil(log2(N)) approximate graph steps.
    Swap test:               N circuit executions (one per vector - quantum brute force).
    Grover:                  floor(π√N / 4) oracle calls.
    """
    if engine_name in ("brute_force_cosine", "faiss_flat_l2", "qiskit_swap_test"):
        return dataset_size
    if engine_name == "faiss_hnsw_l2":
        return max(1, math.ceil(math.log2(max(2, dataset_size))))
    if engine_name in {"hybrid_hnsw_swap_test", "hybrid_hnsw_swap_test_ibm"}:
        return max(1, math.ceil(math.log2(max(2, dataset_size)))) + min(5, dataset_size)
    if engine_name == "qiskit_grover":
        n_padded = max(2, 1 << (dataset_size - 1).bit_length())
        return max(1, int(math.pi / 4 * math.sqrt(n_padded)))
    if engine_name == "qiskit_grover_quantum_prep":
        n_padded = max(2, 1 << (dataset_size - 1).bit_length())
        return max(1, int(math.pi / 4 * math.sqrt(n_padded)))
    return None


def _engine_factories(seed: int | None, dimension: int) -> dict[str, Callable[[], object]]:
    def _simulator() -> AerSimulator:
        return AerSimulator(seed_simulator=seed) if seed is not None else AerSimulator()

    return {
        "brute_force_cosine": lambda: BruteForceCosineEngine(),
        "faiss_flat_l2": lambda: FaissFlatEngine(dimension=dimension),
        "faiss_hnsw_l2": lambda: FaissHnswEngine(dimension=dimension),
        "hybrid_hnsw_swap_test": lambda: HybridHnswSwapTestEngine(
            dimension=dimension,
            backend=_simulator(),
        ),
        "hybrid_hnsw_swap_test_ibm": lambda: HybridHnswSwapTestEngine(
            dimension=dimension,
            backend=load_ibm_backend_from_env(
                min_qubits=1 + 2 * max(1, math.ceil(math.log2(dimension)))
            ),
        ),
        "qiskit_grover": lambda: QiskitGroverEngine(backend=_simulator()),
        "qiskit_swap_test": lambda: QiskitSwapTestEngine(backend=_simulator()),
        "qiskit_grover_quantum_prep": lambda: QiskitGroverQuantumPrepEngine(backend=_simulator()),
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

    def _parse_int_list(key: str) -> List[int]:
        try:
            values = [int(entry) for entry in lists[key]]
        except ValueError as exc:
            raise SystemExit(f"All {key} entries in {path} must be integers.") from exc
        if not values:
            raise SystemExit(f"No {key} listed in {path}.")
        return values

    try:
        top_k = int(scalars["top_k"]) if "top_k" in scalars else 10
    except ValueError as exc:
        raise SystemExit(f"top_k in {path} must be an integer.") from exc

    return BenchmarkSelection(
        classical_engines=lists["classical_engines"],
        quantum_engines=lists["quantum_engines"],
        dimensions=_parse_int_list("dimensions"),
        shots_values=_parse_int_list("shots_values"),
        layers_values=_parse_int_list("layers_values"),
        top_k=top_k,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated benchmarking harness")
    parser.add_argument("--dataset-dir", default="data/images", help="Dataset directory")
    parser.add_argument("--ground-truth", default=None, help="Ground-truth JSONC (defaults to <dataset>/ground_truth.jsonc)")
    parser.add_argument("--config", default="config/benchmarks.yaml", help="Relative or absolute path to benchmark selection YAML")
    parser.add_argument(
        "--dimensions",
        nargs="+",
        type=int,
        default=None,
        help="Override the dimensions from the YAML config (space-separated list)",
    )
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
    shots_values = args.shots_values or selection.shots_values
    layers_values = args.layers_values or selection.layers_values

    ground_truth_path = (
        Path(args.ground_truth).resolve()
        if args.ground_truth
        else (BACKEND_ROOT / "data" / "ground_truth.jsonc").resolve()
    )

    queries = load_benchmark_queries(ground_truth_path)

    storage = DatabaseStorage()
    stored_vectors = storage.load_image_vectors()
    if not stored_vectors:
        raise SystemExit(
            "No image vectors found in the database. "
            "Run `python3 scripts/index_dataset.py` first to encode and store image embeddings."
        )

    all_target_ids = {query.target_id for query in queries}
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
                        if storage.has_record((query.id, engine_name, dimension, shots, layers)):
                            print(
                                f"[{engine_name}] skipping query={query.id} dim={dimension} "
                                f"shots={shots} layers={layers} - already in DB"
                            )
                            continue
                        search_kwargs: dict = {"query_vector": query_vector, "top_k": selection.top_k}
                        if is_quantum:
                            search_kwargs.update({"shots": shots, "layers": layers})

                        search_start = perf_counter()
                        result = engine.search(**search_kwargs)
                        search_ms = (perf_counter() - search_start) * 1000
                        total_ms = prep_ms + search_ms

                        meta = result.meta or {}
                        mrr = _mrr([query.target_id], result.ids)
                        parameters: dict = {"dimension": dimension}
                        if is_quantum:
                            parameters.update({"shots": shots, "layers": layers, "quantum_seed": args.quantum_seed})

                        storage.append(
                            BenchmarkResult(
                                query_id=query.id,
                                engine_name=engine.name,
                                dimension=dimension,
                                target_ids=[query.target_id],
                                top_ids=result.ids,
                                mrr=mrr,
                                state_prep_ms=prep_ms if is_quantum else 0.0,
                                search_ms=search_ms,
                                total_ms=total_ms,
                                shots=shots,
                                layers=layers,
                                parameters=parameters,
                                dataset_size=len(dataset_ids),
                                circuit_depth=meta.get("circuit_depth"),
                                num_qubits=meta.get("num_qubits"),
                                oracle_calls=_oracle_calls(engine.name, len(dataset_ids)),
                            )
                        )
                        print(
                            f"[{engine.name}] query={query.id} dim={dimension} "
                            f"shots={shots} layers={layers} "
                            f"mrr={mrr:.3f} total_ms={total_ms:.2f}"
                        )


if __name__ == "__main__":
    main()
