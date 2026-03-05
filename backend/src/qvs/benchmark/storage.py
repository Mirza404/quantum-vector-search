from __future__ import annotations

from abc import ABC, abstractmethod
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .models import BenchmarkResult


class BaseBenchmarkStorage(ABC):
    @abstractmethod
    def has_record(self, key: tuple[str, str, int]) -> bool:
        ...

    @abstractmethod
    def append(self, result: BenchmarkResult) -> None:
        ...


@dataclass
class CsvMarkdownStorage(BaseBenchmarkStorage):
    csv_path: Path
    markdown_path: Path

    def __post_init__(self) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.markdown_path.parent.mkdir(parents=True, exist_ok=True)
        self._fieldnames = [
            "timestamp",
            "query_id",
            "engine_name",
            "dimension",
            "target_id",
            "top_ids",
            "accuracy",
            "state_prep_ms",
            "search_ms",
            "total_ms",
            "parameters",
        ]
        if not self.csv_path.exists():
            with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=self._fieldnames)
                writer.writeheader()
        self._keys = self._load_existing_keys()

    def has_record(self, key: tuple[str, str, int]) -> bool:
        return key in self._keys

    def append(self, result: BenchmarkResult) -> None:
        row = result.as_csv_row()
        with self.csv_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self._fieldnames)
            writer.writerow(row)
        self._keys.add(result.key())
        self._write_report()

    def _load_existing_keys(self) -> set[tuple[str, str, int]]:
        keys: set[tuple[str, str, int]] = set()
        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                try:
                    keys.add((row["query_id"], row["engine_name"], int(row["dimension"])))
                except (KeyError, ValueError):
                    continue
        return keys

    def _write_report(self) -> None:
        rows = self._read_rows()
        if not rows:
            self.markdown_path.write_text("# Benchmark Report\n\nNo runs recorded yet.\n")
            return
        summary: Dict[tuple[str, int], Dict[str, float]] = {}
        counts: Dict[tuple[str, int], int] = {}
        for row in rows:
            key = (row["engine_name"], int(row["dimension"]))
            counts[key] = counts.get(key, 0) + 1
            group = summary.setdefault(key, {"accuracy": 0.0, "total_ms": 0.0})
            group["accuracy"] += float(row["accuracy"])
            group["total_ms"] += float(row["total_ms"])

        lines = ["# Benchmark Report", "", "## Summary by Engine + Dimension", ""]
        lines.append("| Engine | Dimension | Runs | Avg Accuracy | Avg Total ms |")
        lines.append("| ------ | --------- | ---- | ------------ | ------------ |")
        for (engine, dimension), agg in sorted(summary.items()):
            count = counts[(engine, dimension)]
            avg_acc = agg["accuracy"] / count
            avg_total = agg["total_ms"] / count
            lines.append(
                f"| {engine} | {dimension} | {count} | {avg_acc:.3f} | {avg_total:.2f} |"
            )

        lines.append("")
        lines.append("## Latest Runs")
        lines.append("")
        latest = rows[-10:]
        lines.append(
            "| Timestamp | Query | Engine | Dim | Accuracy | Total ms | Targets (top-3) |"
        )
        lines.append("| --------- | ----- | ------ | --- | -------- | --------- | ---------------- |")
        for row in latest:
            top_ids = row["top_ids"].replace("\"", "")
            lines.append(
                f"| {row['timestamp']} | {row['query_id']} | {row['engine_name']} | {row['dimension']} | "
                f"{float(row['accuracy']):.3f} | {float(row['total_ms']):.2f} | {top_ids} |"
            )
        self.markdown_path.write_text("\n".join(lines))

    def _read_rows(self) -> List[Dict[str, str]]:
        with self.csv_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return list(reader)
