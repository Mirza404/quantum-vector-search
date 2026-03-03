from __future__ import annotations

from typing import Any, List
import math

from . import SearchEngineStrategy, SearchResult


class VectorMockEngine(SearchEngineStrategy):
    def __init__(self) -> None:
        self._vectors: List[List[float]] = []
        self._ids: List[str] = []

    @property
    def name(self) -> str:
        return "vector_mock_l2"

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        self._vectors = vectors
        self._ids = ids

    def search(self, *, query_vector: List[float], top_k: int = 10, **params: Any) -> SearchResult:
        def l2(a: List[float], b: List[float]) -> float:
            if len(a) != len(b):
                raise ValueError("dimension mismatch")
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

        scored = []
        for _id, vec in zip(self._ids, self._vectors):
            d = l2(query_vector, vec)
            score = -d  # higher is better
            scored.append((_id, score))

        scored.sort(key=lambda t: t[1], reverse=True)
        top = scored[:top_k]
        return SearchResult(ids=[t[0] for t in top], scores=[t[1] for t in top], meta={"metric": "l2"})
