from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SearchResult:
    ids: List[str]
    scores: List[float]
    meta: Dict[str, Any] | None = None


class SearchEngineStrategy(ABC): #Strategy INTERFACE

    @property
    @abstractmethod
    def name(self) -> str:
        # Human-readable engine identifier (e.g., 'faiss_cosine', 'qiskit_qaoa', 'mock').

    @abstractmethod
    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        """
        Build any necessary index / state for searching.
        - vector engines: build ANN index
        - quantum engines: build circuit / state prep mappings (or whatever you need)
        """

    @abstractmethod
    def search(self, *, query_vector: List[float], top_k: int = 10, **params: Any) -> SearchResult:
        """
        Execute search with parameters (distance metric, shots, layers, etc.).
        params is intentionally open-ended so we can benchmark freely.
        """