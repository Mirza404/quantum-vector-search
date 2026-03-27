from __future__ import annotations

from abc import ABC, abstractmethod

from .models import BenchmarkResult


class BaseBenchmarkStorage(ABC):
    """Strategy interface for persisting benchmark results."""

    @abstractmethod
    def has_record(self, key: tuple[str, str, int]) -> bool:
        """Return True if the storage already contains this (query, engine, dimension) tuple."""

    @abstractmethod
    def append(self, result: BenchmarkResult) -> None:
        """Persist a benchmark result row."""
