from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence


class EmbeddingGenerator(ABC):
    """Strategy interface for turning text into embedding vectors."""

    @abstractmethod
    def embed(self, text: str, *, dimension: int) -> List[float]:
        """Return a deterministic embedding of length == dimension."""

    def embed_many(self, texts: Sequence[str], *, dimension: int) -> List[List[float]]:
        return [self.embed(text, dimension=dimension) for text in texts]
