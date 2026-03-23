from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .base import BaseDataLoader, Dataset, DatasetRecord

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass
class DirectoryDataLoader(BaseDataLoader):
    """Discover images from a directory. Uses the filename stem as the record ID."""

    dataset_dir: Path

    def get_dataset(self) -> Dataset:
        records = list(self._iter_images())
        if not records:
            raise ValueError(f"No images found in {self.dataset_dir}")
        return Dataset(records=records)

    def describe_source(self) -> str:
        return f"DirectoryDataLoader<{self.dataset_dir}>"

    def _iter_images(self) -> Iterator[DatasetRecord]:
        for path in sorted(self.dataset_dir.iterdir()):
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                yield DatasetRecord(id=path.stem, image_path=path.resolve())
