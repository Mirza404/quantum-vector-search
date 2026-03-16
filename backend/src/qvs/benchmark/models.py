from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class BenchmarkQuery:
    id: str
    text: str
    target_ids: List[str]


def load_benchmark_queries(path: Path) -> List[BenchmarkQuery]:
    raw = json.loads(path.read_text())
    return [BenchmarkQuery(**entry) for entry in raw]


@dataclass
class BenchmarkResult:
    query_id: str
    engine_name: str
    dimension: int
    target_ids: List[str]
    top_ids: List[str]
    accuracy: float
    state_prep_ms: float | None
    search_ms: float
    total_ms: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    dataset_size: int = 0
    circuit_depth: int | None = None
    num_qubits: int | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def key(self) -> tuple[str, str, int]:
        return (self.query_id, self.engine_name, self.dimension)

    def as_csv_row(self) -> Dict[str, Any]:
        payload = {
            "timestamp": self.timestamp.isoformat(),
            "query_id": self.query_id,
            "engine_name": self.engine_name,
            "dimension": self.dimension,
            "target_ids": json.dumps(self.target_ids),
            "top_ids": json.dumps(self.top_ids),
            "accuracy": f"{self.accuracy:.4f}",
            "state_prep_ms": f"{self.state_prep_ms:.4f}" if self.state_prep_ms is not None else "",
            "search_ms": f"{self.search_ms:.4f}",
            "total_ms": f"{self.total_ms:.4f}",
            "parameters": json.dumps(self.parameters, sort_keys=True),
        }
        return payload
