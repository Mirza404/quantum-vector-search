from __future__ import annotations

from typing import Any, List

import faiss
import numpy as np

from .base import SearchEngineStrategy, SearchResult


def _l2_normalize_rows(matrix: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalisation with zero-norm protection."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


class FaissFlatEngine(SearchEngineStrategy):
    """Thin wrapper around Faiss IndexFlatL2 so it matches our strategy interface."""

    def __init__(self, *, dimension: int) -> None:
        self._dim = dimension
        self._index = faiss.IndexFlatL2(dimension)
        self._ids: List[str] = []

    @property
    def name(self) -> str:
        return "faiss_flat_l2"

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if not vectors:
            raise ValueError("cannot build Faiss index with no vectors")
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        if len(vectors[0]) != self._dim:
            raise ValueError(f"expected vectors of dimension {self._dim}")
        self._index.reset()
        self._ids = ids
        matrix = np.asarray(vectors, dtype="float32")
        # Truncating CLIP vectors from 512 to a smaller dim breaks their unit norm.
        # Re-normalising here makes L2 ranking equivalent to cosine ranking, which is
        # what brute_force_cosine uses as ground truth.
        matrix = _l2_normalize_rows(matrix)
        self._index.add(matrix)

    def search(self, *, query_vector: List[float], top_k: int = 10, **params: Any) -> SearchResult:
        if len(query_vector) != self._dim:
            raise ValueError(f"query vector dimension mismatch (expected {self._dim})")
        q = np.asarray([query_vector], dtype="float32")
        q = _l2_normalize_rows(q)
        distances, indices = self._index.search(q, top_k)
        hits = indices[0]
        scores = -distances[0]  # convert L2 distance into “higher is better”
        result_ids = [self._ids[i] for i in hits if i >= 0]
        result_scores = [scores[idx] for idx, i in enumerate(hits) if i >= 0]
        return SearchResult(ids=result_ids, scores=result_scores, meta={"metric": "l2"})
