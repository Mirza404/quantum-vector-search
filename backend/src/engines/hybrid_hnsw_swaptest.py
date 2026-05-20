from __future__ import annotations

from typing import Any, List

from qiskit_aer import AerSimulator

from .base import SearchEngineStrategy, SearchResult
from .faiss_hnsw import FaissHnswEngine
from .qiskit_swaptest import QiskitSwapTestEngine


class HybridHnswSwapTestEngine(SearchEngineStrategy):
    """Classical HNSW candidate retrieval followed by quantum swap-test reranking."""

    def __init__(
        self,
        *,
        dimension: int,
        candidate_pool_size: int = 5,
        backend: AerSimulator | None = None,
    ) -> None:
        if candidate_pool_size <= 0:
            raise ValueError("candidate_pool_size must be positive")
        self._dimension = dimension
        self._candidate_pool_size = candidate_pool_size
        self._backend = backend
        self._hnsw = FaissHnswEngine(dimension=dimension)
        self._vectors_by_id: dict[str, List[float]] = {}
        self._ids: List[str] = []

    @property
    def name(self) -> str:
        return "hybrid_hnsw_swap_test"

    def build_index(
        self,
        *,
        vectors: List[List[float]],
        ids: List[str],
        **params: Any,
    ) -> None:
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        if not vectors:
            raise ValueError("cannot build hybrid index with no vectors")
        if len(vectors[0]) != self._dimension:
            raise ValueError(f"expected vectors of dimension {self._dimension}")

        self._ids = ids
        self._vectors_by_id = dict(zip(ids, vectors, strict=True))
        self._hnsw.build_index(vectors=vectors, ids=ids, **params)

    def search(
        self,
        *,
        query_vector: List[float],
        top_k: int = 10,
        shots: int = 1024,
        **params: Any,
    ) -> SearchResult:
        if not self._ids:
            raise RuntimeError("call build_index() before search()")

        candidate_pool_size = int(params.get("candidate_pool_size", self._candidate_pool_size))
        if candidate_pool_size <= 0:
            raise ValueError("candidate_pool_size must be positive")

        candidate_k = min(max(top_k, candidate_pool_size), len(self._ids))
        candidates = self._hnsw.search(
            query_vector=query_vector,
            top_k=candidate_k,
            ef_search=params.get("ef_search"),
        )
        candidate_ids = candidates.ids[:candidate_pool_size]
        candidate_vectors = [self._vectors_by_id[id_] for id_ in candidate_ids]

        swap_test = QiskitSwapTestEngine(backend=self._backend)
        swap_test.build_index(vectors=candidate_vectors, ids=candidate_ids)
        reranked = swap_test.search(
            query_vector=query_vector,
            top_k=min(top_k, len(candidate_ids)),
            shots=shots,
        )

        quantum_meta = reranked.meta or {}
        return SearchResult(
            ids=reranked.ids,
            scores=reranked.scores,
            meta={
                "hybrid": True,
                "classical_prefilter": "faiss_hnsw_l2",
                "quantum_reranker": "qiskit_swap_test",
                "candidate_pool_size": len(candidate_ids),
                "shots": shots,
                "circuit_depth": quantum_meta.get("circuit_depth"),
                "num_qubits": quantum_meta.get("num_qubits"),
                "score_semantics": "hnsw_prefilter_swap_test_rerank",
            },
        )
