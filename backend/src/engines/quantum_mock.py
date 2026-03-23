from __future__ import annotations

import math
import random
from typing import Any, List

import numpy as np

from qvs.engines import SearchEngineStrategy, SearchResult


class QuantumMockEngine(SearchEngineStrategy):
    """Toy engine that mimics noisy quantum results for benchmarks."""

    def __init__(self, *, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._matrix: np.ndarray | None = None
        self._ids: List[str] = []
        self._num_qubits: int = 0

    @property
    def name(self) -> str:
        return "quantum_mock_sampler"

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if not vectors:
            raise ValueError("quantum_mock requires at least one vector")
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids length mismatch")
        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        self._matrix = matrix / norms
        self._ids = ids
        # Theoretical qubit count: amplitude encoding requires ceil(log2(n)) qubits
        # to represent n items in superposition.
        self._num_qubits = math.ceil(math.log2(max(len(ids), 2)))

    def search(
        self,
        *,
        query_vector: List[float],
        top_k: int = 10,
        shots: int = 1024,
        layers: int = 2,
        **params: Any,
    ) -> SearchResult:
        if self._matrix is None:
            raise RuntimeError("call build_index() before search()")
        query = np.asarray(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(query)
        if q_norm == 0.0:
            raise ValueError("query vector must be non-zero")
        query = query / q_norm
        base_scores = self._matrix @ query
        noise_scale = layers / max(1, shots)
        noises = np.array([self._rng.gauss(0.0, noise_scale) for _ in base_scores], dtype=np.float32)
        scores = base_scores + noises
        top_k = min(top_k, len(self._ids))
        best_idx = np.argsort(scores)[-top_k:][::-1]
        ids = [self._ids[i] for i in best_idx]
        best_scores = [float(scores[i]) for i in best_idx]
        # circuit_depth proxy: each variational layer acts on all qubits once.
        circuit_depth = layers * self._num_qubits
        meta = {
            "shots": shots,
            "layers": layers,
            "noise_scale": noise_scale,
            "circuit_depth": circuit_depth,
            "num_qubits": self._num_qubits,
        }
        return SearchResult(ids=ids, scores=best_scores, meta=meta)
