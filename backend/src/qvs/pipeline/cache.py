from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterable, Mapping, MutableMapping

import numpy as np


@dataclass
class EmbeddingCacheEntry:
    content_hash: str
    index: int


@dataclass
class EmbeddingCacheSnapshot:
    dimension: int
    entries: Dict[str, EmbeddingCacheEntry]


class EmbeddingCache:
    """Persists embeddings + metadata so we avoid recomputation."""

    def __init__(
        self,
        cache_dir: Path,
        *,
        embeddings_filename: str = "embeddings.npy",
        manifest_filename: str = "manifest.json",
    ) -> None:
        self.cache_dir = cache_dir
        self._embeddings_path = cache_dir / embeddings_filename
        self._manifest_path = cache_dir / manifest_filename

    def load(self) -> EmbeddingCacheSnapshot | None:
        if not self._manifest_path.exists() or not self._embeddings_path.exists():
            return None
        with self._manifest_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        entries = {}
        for _id, entry in raw.get("entries", {}).items():
            content_hash = entry.get("content_hash") or entry.get("text_hash")
            if content_hash is None:
                raise ValueError(f"manifest entry {_id} missing content hash")
            entries[_id] = EmbeddingCacheEntry(content_hash=content_hash, index=int(entry["index"]))
        return EmbeddingCacheSnapshot(dimension=int(raw["dimension"]), entries=entries)

    def load_matrix(self) -> np.ndarray | None:
        if not self._embeddings_path.exists():
            return None
        return np.load(self._embeddings_path)

    def save(self, *, dimension: int, entries: Mapping[str, EmbeddingCacheEntry], matrix: np.ndarray) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(self._embeddings_path, matrix)
        serializable = {
            "dimension": dimension,
            "entries": {
                _id: {"content_hash": entry.content_hash, "index": entry.index}
                for _id, entry in entries.items()
            },
        }
        with self._manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(serializable, handle, indent=2)

    def embeddings_path(self) -> Path:
        return self._embeddings_path

    def manifest_path(self) -> Path:
        return self._manifest_path
