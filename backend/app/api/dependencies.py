"""Shared dependencies for API endpoints.

The benchmark harness reads backend/config/benchmarks.yaml to exhaustively
scan (engine, dimension, shots, layers) combinations. The public API faces a
different problem: pick exactly one configuration per process, allow ops to
override it via environment variables, and memoise heavy objects (CLIP model,
DB connections, etc.) so each request can reuse them.

Defaults are pulled from backend/config/benchmarks.yaml (the same file used by
scripts/run_benchmarks.py). Set environment variables to override them without
editing YAML:

    CLASSICAL_ENGINE=<name>   (fallback: first classical entry)
    QUANTUM_ENGINE=<name>     (fallback: first quantum entry)
    SEARCH_DIMENSION=<int>    (fallback: first dimension entry)
    SEARCH_SHOTS=<int>        (fallback: first shots_values entry)
    SEARCH_LAYERS=<int>       (fallback: first layers_values entry)
    SEARCH_TOP_K=<int>        (fallback: top_k entry)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, List

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

BENCHMARK_CONFIG_PATH = BACKEND_ROOT / "config" / "benchmarks.yaml"

from benchmark import DatabaseStorage, load_benchmark_queries  # noqa: E402
from benchmark.models import BenchmarkQuery  # noqa: E402
from engines import (  # noqa: E402
    BruteForceCosineEngine,
    FaissFlatEngine,
    FaissHnswEngine,
    HybridHnswSwapTestEngine,
    QiskitGroverEngine,
    QiskitGroverQuantumPrepEngine,
    QiskitSwapTestEngine,
    SearchEngineStrategy,
)
from pipeline import CLIPEmbeddingModel  # noqa: E402


@dataclass(frozen=True)
class BenchmarkDefaults:
    classical_engine: str
    quantum_engine: str
    dimension: int
    shots: int
    layers: int
    top_k: int


def _first_list_entry(config: dict[str, Any], key: str, *, fallback: Any) -> Any:
    """Return the first non-null entry for `key` or `fallback`."""
    value = config.get(key)
    if value is None:
        return fallback
    if not isinstance(value, list):
        raise RuntimeError(
            f"Expected '{key}' to be a list in {BENCHMARK_CONFIG_PATH}, found {type(value).__name__}"
        )
    for entry in value:
        if entry is not None:
            return entry
    return fallback


@lru_cache(maxsize=1)
def _load_benchmark_defaults() -> BenchmarkDefaults:
    try:
        raw_config = yaml.safe_load(BENCHMARK_CONFIG_PATH.read_text())
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Benchmark config not found: {BENCHMARK_CONFIG_PATH}. "
            "Ensure backend/config/benchmarks.yaml exists."
        ) from exc
    if raw_config is None:
        raise RuntimeError(
            f"Benchmark config {BENCHMARK_CONFIG_PATH} is empty. Populate it before starting the API."
        )
    if not isinstance(raw_config, dict):
        raise RuntimeError(
            f"Benchmark config {BENCHMARK_CONFIG_PATH} must be a mapping at the top level."
        )

    classical = _first_list_entry(
        raw_config, "classical_engines", fallback="brute_force_cosine"
    )
    quantum = _first_list_entry(
        raw_config, "quantum_engines", fallback="qiskit_swap_test"
    )
    dimension = _first_list_entry(raw_config, "dimensions", fallback=64)
    shots = _first_list_entry(raw_config, "shots_values", fallback=1024)
    layers = _first_list_entry(raw_config, "layers_values", fallback=1)
    top_k = raw_config.get("top_k", 10)

    try:
        return BenchmarkDefaults(
            classical_engine=str(classical),
            quantum_engine=str(quantum),
            dimension=int(dimension),
            shots=int(shots),
            layers=int(layers),
            top_k=int(top_k),
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Invalid numeric value in {BENCHMARK_CONFIG_PATH}: {exc}"
        ) from exc

# ---------------------------------------------------------------------------
# Config defaults from benchmarks.yaml + optional env overrides
# ---------------------------------------------------------------------------

_BENCHMARK_DEFAULTS = _load_benchmark_defaults()

CLASSICAL_ENGINE_NAME = os.getenv(
    "CLASSICAL_ENGINE", _BENCHMARK_DEFAULTS.classical_engine
)
QUANTUM_ENGINE_NAME = os.getenv(
    "QUANTUM_ENGINE", _BENCHMARK_DEFAULTS.quantum_engine
)
SEARCH_DIMENSION = int(
    os.getenv("SEARCH_DIMENSION", str(_BENCHMARK_DEFAULTS.dimension))
)
SEARCH_SHOTS = int(
    os.getenv("SEARCH_SHOTS", str(_BENCHMARK_DEFAULTS.shots))
)
SEARCH_LAYERS = int(
    os.getenv("SEARCH_LAYERS", str(_BENCHMARK_DEFAULTS.layers))
)
SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", str(_BENCHMARK_DEFAULTS.top_k)))

DATA_DIR = BACKEND_ROOT / "data"
IMAGES_DIR = DATA_DIR / "images"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth.jsonc"

# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_engine(name: str, dimension: int) -> SearchEngineStrategy:
    factories = {
        "brute_force_cosine": lambda: BruteForceCosineEngine(),
        "faiss_flat_l2": lambda: FaissFlatEngine(dimension=dimension),
        "faiss_hnsw_l2": lambda: FaissHnswEngine(dimension=dimension),
        "hybrid_hnsw_swap_test": lambda: HybridHnswSwapTestEngine(dimension=dimension),
        "qiskit_swap_test": lambda: QiskitSwapTestEngine(),
        "qiskit_grover": lambda: QiskitGroverEngine(),
        "qiskit_grover_quantum_prep": lambda: QiskitGroverQuantumPrepEngine(),
    }
    if name not in factories:
        raise ValueError(
            f"Unknown engine '{name}'. Available: {', '.join(factories)}"
        )
    return factories[name]()


# ---------------------------------------------------------------------------
# Cached singletons (created once per process)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_queries() -> List[BenchmarkQuery]:
    return load_benchmark_queries(GROUND_TRUTH_PATH)


@lru_cache(maxsize=1)
def get_image_ids() -> List[str]:
    """Sorted list of image IDs available on disk."""
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    return sorted(
        p.stem for p in IMAGES_DIR.iterdir() if p.suffix.lower() in exts
    )


@lru_cache(maxsize=1)
def get_storage() -> DatabaseStorage:
    return DatabaseStorage()


@lru_cache(maxsize=1)
def get_clip_model() -> CLIPEmbeddingModel:
    return CLIPEmbeddingModel(
        model_name=os.getenv("CLIP_MODEL", "ViT-B/32"),
        device=os.getenv("CLIP_DEVICE"),
    )


def get_classical_engine() -> SearchEngineStrategy:
    return _make_engine(CLASSICAL_ENGINE_NAME, SEARCH_DIMENSION)


def get_quantum_engine() -> SearchEngineStrategy:
    return _make_engine(QUANTUM_ENGINE_NAME, SEARCH_DIMENSION)


def get_all_engines() -> list[tuple[SearchEngineStrategy, bool]]:
    """Engines used by live API search.

    IBM hardware is intentionally excluded here. It is exposed only through
    explicit scripts because QPU queue time and Open Plan quota are limited.
    """
    all_engines = [
        ("brute_force_cosine", False),
        ("faiss_flat_l2", False),
        ("faiss_hnsw_l2", False),
        ("hybrid_hnsw_swap_test", True),
        ("qiskit_swap_test", True),
        ("qiskit_grover", True),
        ("qiskit_grover_quantum_prep", True),
    ]
    return [(_make_engine(name, SEARCH_DIMENSION), is_quantum) for name, is_quantum in all_engines]
