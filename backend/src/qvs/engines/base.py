from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class SearchResult:
    ids: List[str]
    scores: List[float]
    meta: Dict[str, Any] | None = None


class SearchEngineStrategy(ABC):
    """Base strategy contract shared by all search engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable identifier (e.g., 'faiss_cosine')."""

    @abstractmethod
    def build_index(self, *, vectors: List[List[float]], ids: List[str], **params: Any) -> None:
        """
        Build any necessary index/state for searching.
        Vector engines might build ANN indexes; quantum engines prepare circuits.
        """

    @abstractmethod
    def search(self, *, query_vector: List[float], top_k: int = 10, **params: Any) -> SearchResult:
        """
        Execute a search using the provided parameters.
        params stays open-ended so implementations can expose engine-specific knobs.
        """
