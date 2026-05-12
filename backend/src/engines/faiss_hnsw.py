from __future__ import annotations

from typing import Any, List

import faiss
import numpy as np

from .base import SearchEngineStrategy, SearchResult


class FaissHNSWEngine(SearchEngineStrategy):
    """
    HNSW (Hierarchical Navigable Small World) approximate nearest neighbor search.
    Uses FAISS's IndexHNSWFlat for production-grade approximate search.
    
    Query time: O(log N) with ~95-99%+ recall in practice on large datasets.
    Widely used at Meta, Spotify, Google for production vector search.
    """

    def __init__(self, *, dimension: int, m: int = 32, ef_construction: int = 200) -> None:
        """
        Initialize HNSW index.
        
        Args:
            dimension: Vector dimensionality
            m: Number of bi-directional links created per node (higher = more accurate, more memory)
            ef_construction: Size of dynamic list (higher = more accurate index building, slower)
        """
        self._dim = dimension
        self._m = m
        self._ef_construction = ef_construction
        self._index = faiss.IndexHNSWFlat(dimension, m)
        self._index.hnsw.efConstruction = ef_construction
        self._ids: List[str] = []

    @property
    def name(self) -> str:
        return "faiss_hnsw_l2"

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if not vectors:
            raise ValueError("cannot build HNSW index with no vectors")
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
        scores = -distances[0]  # convert L2 distance into "higher is better"
        result_ids = [self._ids[i] for i in hits if i >= 0]
        result_scores = [scores[idx] for idx, i in enumerate(hits) if i >= 0]
        return SearchResult(ids=result_ids, scores=result_scores, meta={"metric": "l2", "approximate": True})
