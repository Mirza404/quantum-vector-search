from __future__ import annotations

import hashlib
import random
from typing import List

from .base import EmbeddingGenerator


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
