from __future__ import annotations

from typing import Any, List

import faiss
import numpy as np

from .base import SearchEngineStrategy, SearchResult


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
        self._index.add(matrix)

    def search(self, *, query_vector: List[float], top_k: int = 10, **params: Any) -> SearchResult:
        if len(query_vector) != self._dim:
            raise ValueError(f"query vector dimension mismatch (expected {self._dim})")
        q = np.asarray([query_vector], dtype="float32")
        distances, indices = self._index.search(q, top_k)
        hits = indices[0]
        scores = -distances[0]  # convert L2 distance into “higher is better”
        result_ids = [self._ids[i] for i in hits if i >= 0]
        result_scores = [scores[idx] for idx, i in enumerate(hits) if i >= 0]
        return SearchResult(ids=result_ids, scores=result_scores, meta={"metric": "l2"})
