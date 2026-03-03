from __future__ import annotations

from typing import Any, List
import math
import random

from . import SearchEngineStrategy, SearchResult


class QuantumMockEngine(SearchEngineStrategy):
    def __init__(self, *, seed: int | None = None) -> None:
        self._vectors: List[List[float]] = []
        self._ids: List[str] = []
        self._rng = random.Random(seed)

    @property
    def name(self) -> str:
        return "quantum_mock_overlap"

    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        self._vectors = vectors
        self._ids = ids

    def search(self, *, query_vector: List[float], top_k: int = 10, **params: Any) -> SearchResult:
        if not self._vectors:
            raise RuntimeError("call build_index before search")

        if not query_vector:
            raise ValueError("query_vector must not be empty")

        shots = int(params.get("shots", 1024))
        layers = int(params.get("layers", 1))
        layers = max(layers, 1)
        shots = max(shots, 1)

        def normalize(vec: List[float]) -> List[float]:
            norm = math.sqrt(sum(x * x for x in vec))
            if norm == 0:
                return [0.0 for _ in vec]
            return [x / norm for x in vec]

        query_unit = normalize(query_vector)
        dim = len(query_vector)

        scored = []
        noise_scale = (layers * 0.05) / math.sqrt(shots)
        for _id, vec in zip(self._ids, self._vectors):
            if len(vec) != dim:
                raise ValueError("all indexed vectors must have the same dimension as the query vector")
            vec_unit = normalize(vec)
            amplitude = sum(q * v for q, v in zip(query_unit, vec_unit))
            amplitude = max(min(amplitude, 1.0), -1.0)
            probability = amplitude * amplitude
            score = probability + self._rng.gauss(0.0, noise_scale)
            scored.append((_id, score))

        scored.sort(key=lambda t: t[1], reverse=True)
        top = scored[:top_k]
        meta = {
            "shots": shots,
            "layers": layers,
            "noise_scale": noise_scale,
            "score_semantics": "probability + gaussian_noise",
        }
        return SearchResult(ids=[t[0] for t in top], scores=[t[1] for t in top], meta=meta)
