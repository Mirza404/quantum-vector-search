from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class BenchmarkQuery:
    id: str
    text: str

    @property
    def target_id(self) -> str:
        """Derive the target image ID from the query ID by stripping the 'query_' prefix."""
        return self.id.removeprefix("query_")


def _strip_jsonc_comments(text: str) -> str:
    """Strip // line comments so JSONC files can be parsed by the standard json module."""
    return re.sub(r"//[^\n]*", "", text)


def load_benchmark_queries(path: Path) -> List[BenchmarkQuery]:
    raw = json.loads(_strip_jsonc_comments(path.read_text()))
    return [BenchmarkQuery(id=entry["id"], text=entry["text"]) for entry in raw]


@dataclass
class BenchmarkResult:
    query_id: str
    engine_name: str
    dimension: int
    target_ids: List[str]
    top_ids: List[str]
    mrr: float
    state_prep_ms: float | None
    search_ms: float
    total_ms: float
    shots: int | None = None
    layers: int | None = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dataset_size: int = 0
    circuit_depth: int | None = None
    num_qubits: int | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def key(self) -> tuple[str, str, int, int | None, int | None]:
        return (self.query_id, self.engine_name, self.dimension, self.shots, self.layers)
