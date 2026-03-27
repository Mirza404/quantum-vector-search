from __future__ import annotations

from typing import Any, List

import numpy as np

from .base import SearchEngineStrategy, SearchResult


class BruteForceCosineEngine(SearchEngineStrategy):
    """Deterministic cosine-similarity search used for quick benchmarks."""

    def __init__(self) -> None:
        self._matrix: np.ndarray | None = None
        self._ids: List[str] = []

    @property
    def name(self) -> str:
        return "brute_force_cosine"

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if not vectors:
            raise ValueError("brute_force_cosine requires at least one vector")
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        self._matrix = matrix / norms
        self._ids = ids

    def search(self, *, query_vector: List[float], top_k: int = 10, **params: Any) -> SearchResult:
        if self._matrix is None:
            raise RuntimeError("call build_index() before search()")
        query = np.asarray(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(query)
        if q_norm == 0.0:
            raise ValueError("query vector must be non-zero")
        query = query / q_norm
        scores = self._matrix @ query
        top_k = min(top_k, len(self._ids))
        best_idx = np.argsort(scores)[-top_k:][::-1]
        ids = [self._ids[i] for i in best_idx]
        best_scores = [float(scores[i]) for i in best_idx]
        return SearchResult(ids=ids, scores=best_scores, meta={"metric": "cosine"})
