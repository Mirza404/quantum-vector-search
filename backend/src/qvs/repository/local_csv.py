from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path
from typing import Iterator

from .base import BaseDataLoader, Dataset, DatasetRecord


@dataclass
class LocalCSVDataLoader(BaseDataLoader):
    """Load dataset metadata from a local CSV file."""

    dataset_dir: Path
    metadata_filename: str = "metadata.csv"

    def _metadata_path(self) -> Path:
        path = self.dataset_dir / self.metadata_filename
        if not path.exists():
            raise FileNotFoundError(f"metadata file not found: {path}")
        return path

    def get_dataset(self) -> Dataset:
        records = list(self._iter_rows())
        if not records:
            raise ValueError(f"dataset at {self.dataset_dir} is empty")
        return Dataset(records=records)

    def describe_source(self) -> str:
        return f"LocalCSVDataLoader<{self._metadata_path()}>"

    def _iter_rows(self) -> Iterator[DatasetRecord]:
        metadata_path = self._metadata_path()
        with metadata_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"id", "text", "image_path"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"metadata missing columns: {sorted(missing)}")
            for row in reader:
                image_path = (self.dataset_dir / row["image_path"]).resolve()
                yield DatasetRecord(
                    id=row["id"].strip(),
                    text=row["text"].strip(),
                    image_path=image_path,
                )
