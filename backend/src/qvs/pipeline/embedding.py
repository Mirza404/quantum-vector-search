from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Sequence
import hashlib
import random


class EmbeddingGenerator(ABC):
    """Strategy interface for turning text into embedding vectors."""

    @abstractmethod
    def embed(self, text: str, *, dimension: int) -> List[float]:
        """Return a deterministic embedding of length == dimension."""

    def embed_many(self, texts: Sequence[str], *, dimension: int) -> List[List[float]]:
        return [self.embed(text, dimension=dimension) for text in texts]


class MockCLIPEmbeddingGenerator(EmbeddingGenerator):
    """Deterministic pseudo-CLIP implementation used for local testing."""

    def __init__(self, *, seed: str = "mock-clip") -> None:
        self._seed = seed

    def embed(self, text: str, *, dimension: int) -> List[float]:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        digest = hashlib.sha256(f"{self._seed}:{text}".encode("utf-8")).hexdigest()
        rng = random.Random(int(digest, 16))
        vector = [rng.uniform(-1.0, 1.0) for _ in range(dimension)]
        return vector
