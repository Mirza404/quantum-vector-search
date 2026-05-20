from __future__ import annotations

from abc import ABC, abstractmethod

from .models import BenchmarkResult


class BaseBenchmarkStorage(ABC):
    """Strategy interface for persisting benchmark results."""

    @abstractmethod
    def has_record(self, key: tuple[str, str, int, int | None, int | None]) -> bool:
        """Return True if storage already contains this query/engine/dimension/shots/layers run."""

    @abstractmethod
    def append(self, result: BenchmarkResult) -> None:
        """Persist a benchmark result row."""
