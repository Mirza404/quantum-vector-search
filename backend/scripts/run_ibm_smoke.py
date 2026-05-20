#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from benchmark.db_storage import _bootstrap_env  # noqa: E402
from engines.hybrid_hnsw_swaptest import HybridHnswSwapTestEngine  # noqa: E402
from engines.ibm_backend import load_ibm_backend_from_env  # noqa: E402


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
    backend = load_ibm_backend_from_env(min_qubits=3)
    engine = HybridHnswSwapTestEngine(
        dimension=2,
        candidate_pool_size=2,
        backend=backend,
    )
    engine.build_index(
        vectors=[[1.0, 0.0], [0.0, 1.0], [0.7071, 0.7071]],
        ids=["target", "opposite", "mixed"],
    )
    result = engine.search(query_vector=[1.0, 0.0], top_k=2, shots=32)
    print("IBM hybrid smoke result")
    print("ids:", result.ids)
    print("scores:", [round(score, 3) for score in result.scores])
    print("meta:", result.meta)
    _print_usage("after")


if __name__ == "__main__":
    main()
