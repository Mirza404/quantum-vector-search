"""Shared dependencies for API endpoints.

Engine selection is driven by environment variables so the strategy can be
swapped without code changes:

    CLASSICAL_ENGINE=brute_force_cosine   (default) | faiss_flat_l2
    QUANTUM_ENGINE=quantum_mock_sampler   (default) | qiskit_swap_test
    SEARCH_DIMENSION=64                   (default)
    SEARCH_SHOTS=1024                     (default)
    SEARCH_LAYERS=1                       (default)
    SEARCH_TOP_K=10                       (default)
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import List

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from benchmark import DatabaseStorage, load_benchmark_queries
from benchmark.models import BenchmarkQuery
from engines import (
    BruteForceCosineEngine,
    FaissFlatEngine,
    QiskitSwapTestEngine,
    QuantumMockEngine,
    SearchEngineStrategy,
)
from pipeline import CLIPEmbeddingModel

# ---------------------------------------------------------------------------
# Config from env
# ---------------------------------------------------------------------------

CLASSICAL_ENGINE_NAME = os.getenv("CLASSICAL_ENGINE", "brute_force_cosine")
QUANTUM_ENGINE_NAME = os.getenv("QUANTUM_ENGINE", "quantum_mock_sampler")
SEARCH_DIMENSION = int(os.getenv("SEARCH_DIMENSION", "64"))
SEARCH_SHOTS = int(os.getenv("SEARCH_SHOTS", "1024"))
SEARCH_LAYERS = int(os.getenv("SEARCH_LAYERS", "1"))
SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "10"))

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
        "quantum_mock_sampler": lambda: QuantumMockEngine(seed=42),
        "qiskit_swap_test": lambda: QiskitSwapTestEngine(),
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
