from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class DatasetRecord:
    """Single image item in the dataset."""

    id: str
    image_path: Path


@dataclass(frozen=True)
class Dataset:
    """Simple in-memory collection of dataset records."""

    records: Sequence[DatasetRecord]

    def ids(self) -> List[str]:
        return [record.id for record in self.records]


class BaseDataLoader(ABC):
    """Strategy interface for retrieving benchmark datasets."""

    @abstractmethod
    def get_dataset(self) -> Dataset:
        """Return the immutable dataset snapshot."""

    @abstractmethod
    def describe_source(self) -> str:
        """Explain where the data came from (for logging/debug)."""
