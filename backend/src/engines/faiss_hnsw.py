from __future__ import annotations

from typing import Any, List

import faiss
import numpy as np

from .base import SearchEngineStrategy, SearchResult
from .faiss_flat import _l2_normalize_rows


class FaissHnswEngine(SearchEngineStrategy):
    """FAISS HNSW approximate nearest-neighbor index using L2 distance."""

    def __init__(
        self,
        *,
        dimension: int,
        m: int = 16,
        ef_construction: int = 40,
        ef_search: int = 32,
    ) -> None:
        if m <= 0:
            raise ValueError("m must be positive")
        if ef_construction <= 0:
            raise ValueError("ef_construction must be positive")
        if ef_search <= 0:
            raise ValueError("ef_search must be positive")
        self._dim = dimension
        self._m = m
        self._ef_construction = ef_construction
        self._ef_search = ef_search
        self._index = self._new_index()
        self._ids: List[str] = []

    @property
    def name(self) -> str:
        return "faiss_hnsw_l2"

    def _new_index(self) -> faiss.IndexHNSWFlat:
        index = faiss.IndexHNSWFlat(self._dim, self._m)
        index.hnsw.efConstruction = self._ef_construction
        index.hnsw.efSearch = self._ef_search
        return index

    def build_index(
        self,
        *,
        vectors: List[List[float]],
        ids: List[str],
        **params: Any,
    ) -> None:
        if not vectors:
            raise ValueError("cannot build Faiss HNSW index with no vectors")
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        if len(vectors[0]) != self._dim:
            raise ValueError(f"expected vectors of dimension {self._dim}")

        self._index = self._new_index()
        self._ids = ids
        matrix = np.asarray(vectors, dtype="float32")
        # See faiss_flat.py: truncated CLIP vectors are no longer unit-norm, so
        # L2 ranking diverges from cosine. Renormalising restores equivalence.
        matrix = _l2_normalize_rows(matrix)
        self._index.add(matrix)

    def search(
        self,
        *,
        query_vector: List[float],
        top_k: int = 10,
        **params: Any,
    ) -> SearchResult:
        if len(query_vector) != self._dim:
            raise ValueError(f"query vector dimension mismatch (expected {self._dim})")
        if not self._ids:
            raise RuntimeError("call build_index() before search()")

        ef_search = params.get("ef_search")
        if ef_search is not None:
            if int(ef_search) <= 0:
                raise ValueError("ef_search must be positive")
            self._index.hnsw.efSearch = int(ef_search)

        q = np.asarray([query_vector], dtype="float32")
        q = _l2_normalize_rows(q)
        distances, indices = self._index.search(q, top_k)
        hits = indices[0]
        scores = -distances[0]
        result_ids = [self._ids[i] for i in hits if i >= 0]
        result_scores = [float(scores[idx]) for idx, i in enumerate(hits) if i >= 0]
        return SearchResult(
            ids=result_ids,
            scores=result_scores,
            meta={
                "metric": "l2",
                "index": "hnsw",
                "m": self._m,
                "ef_construction": self._ef_construction,
                "ef_search": self._index.hnsw.efSearch,
            },
        )
