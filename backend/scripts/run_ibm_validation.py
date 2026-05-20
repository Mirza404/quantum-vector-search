#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from time import perf_counter

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from benchmark import BenchmarkResult, DatabaseStorage, load_benchmark_queries  # noqa: E402
from benchmark.db_storage import _bootstrap_env  # noqa: E402
from engines.hybrid_hnsw_swaptest import HybridHnswSwapTestEngine  # noqa: E402
from engines.ibm_backend import load_ibm_backend_from_env  # noqa: E402
from pipeline import CLIPEmbeddingModel  # noqa: E402

ENGINE_NAME = "hybrid_hnsw_swap_test_ibm"
DIMENSION = 2
SHOTS = 32
LAYERS = 1
TOP_K = 2
CANDIDATE_POOL_SIZE = 2


def _mrr(target_id: str, ranked_ids: list[str]) -> float:
    for rank, item in enumerate(ranked_ids, start=1):
        if item == target_id:
            return 1.0 / rank
    return 0.0


def _print_usage(label: str) -> None:
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        import os

        service = QiskitRuntimeService(
            channel="ibm_quantum_platform",
            token=os.getenv("IBM_QUANTUM_TOKEN"),
            instance=os.getenv("IBM_QUANTUM_INSTANCE"),
        )
        print(f"{label} usage:", service.usage())
    except Exception as exc:
        print(f"{label} usage: unavailable ({exc})")


def main() -> None:
    _bootstrap_env()
    _print_usage("before")

    storage = DatabaseStorage()
    queries = load_benchmark_queries(BACKEND_ROOT / "data" / "ground_truth.jsonc")
    stored_vectors = storage.load_image_vectors()
    if not stored_vectors:
        raise SystemExit("No image vectors found. Run scripts/index_dataset.py first.")

    dataset_ids = list(stored_vectors.keys())
    dataset_matrix = np.array([stored_vectors[id_] for id_ in dataset_ids], dtype=np.float32)
    vectors = dataset_matrix[:, :DIMENSION].tolist()

    clip_model = CLIPEmbeddingModel(batch_size=16)
    query_matrix = clip_model.encode_texts([query.text for query in queries])

    backend = load_ibm_backend_from_env(min_qubits=3)

    for idx, query in enumerate(queries, start=1):
        key = (query.id, ENGINE_NAME, DIMENSION, SHOTS, LAYERS)
        if storage.has_record(key):
            print(f"[{idx}/{len(queries)}] skip {query.id} - already in DB")
            continue

        query_vector = query_matrix[idx - 1][:DIMENSION].astype(np.float32).tolist()
        engine = HybridHnswSwapTestEngine(
            dimension=DIMENSION,
            candidate_pool_size=CANDIDATE_POOL_SIZE,
            backend=backend,
        )

        prep_start = perf_counter()
        engine.build_index(vectors=vectors, ids=dataset_ids)
        prep_ms = (perf_counter() - prep_start) * 1000

        search_start = perf_counter()
        result = engine.search(
            query_vector=query_vector,
            top_k=TOP_K,
            shots=SHOTS,
            candidate_pool_size=CANDIDATE_POOL_SIZE,
        )
        search_ms = (perf_counter() - search_start) * 1000
        total_ms = prep_ms + search_ms
        meta = result.meta or {}

        score = _mrr(query.target_id, result.ids)
        storage.append(
            BenchmarkResult(
                query_id=query.id,
                engine_name=ENGINE_NAME,
                dimension=DIMENSION,
                target_ids=[query.target_id],
                top_ids=result.ids,
                mrr=score,
                state_prep_ms=prep_ms,
                search_ms=search_ms,
                total_ms=total_ms,
                shots=SHOTS,
                layers=LAYERS,
                parameters={
                    "dimension": DIMENSION,
                    "shots": SHOTS,
                    "layers": LAYERS,
                    "top_k": TOP_K,
                    "candidate_pool_size": CANDIDATE_POOL_SIZE,
                    "hardware": "ibm_quantum",
                },
                dataset_size=len(dataset_ids),
                circuit_depth=meta.get("circuit_depth"),
                num_qubits=meta.get("num_qubits"),
                oracle_calls=CANDIDATE_POOL_SIZE,
            )
        )
        print(
            f"[{idx}/{len(queries)}] {query.id} mrr={score:.3f} "
            f"ids={result.ids} total_ms={total_ms:.1f}"
        )

    _print_usage("after")


if __name__ == "__main__":
    main()
