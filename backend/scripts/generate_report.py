#!/usr/bin/env python3
"""Generate a Markdown benchmark report from the database.

Usage (from repo root):
    python3 backend/scripts/generate_report.py
    python3 backend/scripts/generate_report.py --out docs/report.md

KPIs
----
Cross-engine comparisons focus solely on result quality:
  - Weighted accuracy  : positional score (1.0 / 0.66 / 0.33) — NDCG-lite
  - Recall@K           : was any target present anywhere in top-K?
  - MRR                : 1 / rank of the first relevant result

Speed (ms) is reported *per engine* only to show how each engine scales with
dimension.  Cross-engine wall-clock comparisons are intentionally omitted:
the quantum engine runs on a classical simulator, so its timing reflects
circuit-simulation overhead rather than real quantum hardware latency.

Quantum-specific KPI:
  - Shots-to-accuracy  : accuracy achieved at each shots value, showing the
                         minimum measurement budget needed to reach a target.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from qvs.benchmark.db_storage import _bootstrap_env  # noqa: E402

_bootstrap_env()


# ---------------------------------------------------------------------------
# DB fetch
# ---------------------------------------------------------------------------

def _fetch_rows(dsn: str) -> list[dict]:
    import psycopg
    import psycopg.rows

    with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id, recorded_at, query_id, engine_name, dimension,
                    target_ids, top_ids,
                    accuracy, state_prep_ms, search_ms, total_ms,
                    parameters, dataset_size, circuit_depth, num_qubits
                FROM benchmark_results
                ORDER BY engine_name, dimension, query_id
            """)
            return cur.fetchall()


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _recall(target_ids: list[str], top_ids: list[str]) -> float:
    """Fraction of target_ids found in top_ids."""
    if not target_ids:
        return 0.0
    return sum(1 for t in target_ids if t in top_ids) / len(target_ids)


def _get_top_k(row: dict) -> int:
    return (row.get("parameters") or {}).get("top_k", 0)


def _mrr(target_ids: list[str], top_ids: list[str]) -> float:
    """Reciprocal rank of the first relevant result (1-indexed). 0 if not found."""
    for rank, item in enumerate(top_ids, start=1):
        if item in target_ids:
            return 1.0 / rank
    return 0.0


def _fmt(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}"


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return "| " + " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cells)) + " |"

    separator = "| " + " | ".join("-" * w for w in col_widths) + " |"
    lines = [fmt_row(headers), separator] + [fmt_row(r) for r in rows]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def _section_overview(rows: list[dict]) -> str:
    engines = sorted({r["engine_name"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})
    queries = sorted({r["query_id"] for r in rows})
    timestamps = [r["recorded_at"] for r in rows]
    earliest = min(timestamps).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    latest = max(timestamps).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    top_k_vals = sorted({_get_top_k(r) for r in rows} - {0})
    lines = [
        "## Overview\n",
        "| Metric | Value |",
        "|---|---|",
        f"| Total runs | {len(rows)} |",
        f"| Engines | {', '.join(f'`{e}`' for e in engines)} |",
        f"| Dimensions | {', '.join(str(d) for d in dimensions)} |",
        f"| top_k values | {', '.join(str(k) for k in top_k_vals)} |",
        f"| Queries | {', '.join(f'`{q}`' for q in queries)} |",
        f"| Earliest run | {earliest} |",
        f"| Latest run | {latest} |",
    ]
    return "\n".join(lines)


def _section_winner(rows: list[dict]) -> str:
    """Top-line summary: which engine won on each quality KPI."""
    by_engine: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        e = r["engine_name"]
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        by_engine[e]["accuracy"].append(r["accuracy"])
        by_engine[e]["recall"].append(_recall(targets, top))
        by_engine[e]["mrr"].append(_mrr(targets, top))

    def _winner(metric: str) -> str:
        scores = {e: _avg(d[metric]) for e, d in by_engine.items()}
        best = max(scores.values())
        winners = [e for e, s in scores.items() if s == best]
        if len(winners) == len(scores):
            return f"Tie ({_pct(best) if metric != 'mrr' else _fmt(best, 3)})"
        return f"`{'`, `'.join(sorted(winners))}` ({_pct(best) if metric != 'mrr' else _fmt(best, 3)})"

    lines = [
        "## Results Summary\n",
        "| KPI | Winner |",
        "|---|---|",
        f"| Weighted Accuracy | {_winner('accuracy')} |",
        f"| Recall@K | {_winner('recall')} |",
        f"| MRR | {_winner('mrr')} |",
    ]
    return "\n".join(lines)


def _section_kpi_summary(rows: list[dict]) -> str:
    """Cross-engine quality KPIs: weighted accuracy, Recall@K, MRR."""
    by_engine: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        e = r["engine_name"]
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        by_engine[e]["accuracy"].append(r["accuracy"])
        by_engine[e]["recall"].append(_recall(targets, top))
        by_engine[e]["mrr"].append(_mrr(targets, top))

    headers = ["Engine", "Avg Weighted Accuracy", "Recall@K", "MRR", "Runs"]
    table_rows = []
    for engine in sorted(by_engine):
        d = by_engine[engine]
        table_rows.append([
            f"`{engine}`",
            _pct(_avg(d["accuracy"])),
            _pct(_avg(d["recall"])),
            _fmt(_avg(d["mrr"]), 3),
            str(len(d["accuracy"])),
        ])

    note = (
        "> **Metrics**\n"
        "> - **Weighted Accuracy** — positional score: 1.0 (rank 1) / 0.66 (rank 2) / 0.33 (rank 3). NDCG-lite.\n"
        "> - **Recall@K** — did the relevant item appear anywhere in the top-K results?\n"
        "> - **MRR** — Mean Reciprocal Rank. Higher = relevant result ranked closer to position 1.\n"
    )
    return "## Quality KPIs by Engine\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_quality_by_dimension(rows: list[dict]) -> str:
    """Per-engine quality metrics broken down by dimension."""
    data: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        key = (r["engine_name"], r["dimension"])
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        data[key]["accuracy"].append(r["accuracy"])
        data[key]["recall"].append(_recall(targets, top))
        data[key]["mrr"].append(_mrr(targets, top))

    engines = sorted({r["engine_name"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})

    headers = ["Engine", "Dimension", "Weighted Accuracy", "Recall@K", "MRR"]
    table_rows = []
    for engine in engines:
        for dim in dimensions:
            key = (engine, dim)
            if key not in data:
                continue
            d = data[key]
            table_rows.append([
                f"`{engine}`",
                str(dim),
                _pct(_avg(d["accuracy"])),
                _pct(_avg(d["recall"])),
                _fmt(_avg(d["mrr"]), 3),
            ])

    note = "> Quality metrics only. Speed is excluded from cross-engine comparisons — see per-engine scaling below.\n"
    return "## Quality by Dimension\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_quality_by_top_k(rows: list[dict]) -> str:
    """Shows how quality metrics change as top_k varies — the core scaling experiment."""
    top_k_vals = sorted({_get_top_k(r) for r in rows} - {0})
    if len(top_k_vals) < 2:
        return ""

    data: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        key = (r["engine_name"], _get_top_k(r))
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        data[key]["accuracy"].append(r["accuracy"])
        data[key]["recall"].append(_recall(targets, top))
        data[key]["mrr"].append(_mrr(targets, top))

    engines = sorted({r["engine_name"] for r in rows})
    headers = ["Engine", "top_k", "Weighted Accuracy", "Recall@K", "MRR"]
    table_rows = []
    for engine in engines:
        for k in top_k_vals:
            key = (engine, k)
            if key not in data:
                continue
            d = data[key]
            table_rows.append([
                f"`{engine}`",
                str(k),
                _pct(_avg(d["accuracy"])),
                _pct(_avg(d["recall"])),
                _fmt(_avg(d["mrr"]), 3),
            ])

    note = "> A good engine scores high even at small top_k. Accuracy dropping sharply as top_k decreases means the engine struggles to rank correct results near the top.\n"
    return "## Quality by top_k\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_circuit_complexity(rows: list[dict]) -> str:
    """Quantum circuit resource usage broken down by dimension and dataset size."""
    quantum_rows = [r for r in rows if r.get("circuit_depth") is not None]
    if not quantum_rows:
        return ""

    # Group by (engine, dimension, dataset_size)
    data: dict[tuple[str, int, int], dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for r in quantum_rows:
        key = (r["engine_name"], r["dimension"], r["dataset_size"])
        data[key]["circuit_depth"].append(r["circuit_depth"])
        data[key]["num_qubits"].append(r["num_qubits"])

    headers = ["Engine", "Dimension", "Dataset Size", "Circuit Depth", "Qubits"]
    table_rows = []
    for (engine, dim, ds) in sorted(data):
        d = data[(engine, dim, ds)]
        # These are constant per (engine, dim, dataset_size) — just take the first value.
        table_rows.append([
            f"`{engine}`",
            str(dim),
            str(ds),
            str(d["circuit_depth"][0]),
            str(d["num_qubits"][0]),
        ])

    note = (
        "> Circuit metrics are hardware-agnostic cost proxies.\n"
        "> **Circuit depth** = number of sequential gate layers; deeper circuits are more susceptible to decoherence on real hardware.\n"
        "> **Qubits** = number of qubits required; more qubits = harder to allocate on near-term devices.\n"
        "> For the mock engine these are theoretical estimates based on amplitude encoding.\n"
        "> For the swap-test engine these are extracted from the actual compiled Qiskit circuit.\n"
    )
    return "## Quantum Circuit Complexity\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_speed_scaling(rows: list[dict]) -> str:
    """Per-engine speed scaling with dimension. Cross-engine comparison intentionally omitted."""
    data: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        key = (r["engine_name"], r["dimension"])
        data[key]["search_ms"].append(r["search_ms"])
        data[key]["total_ms"].append(r["total_ms"])
        if r["state_prep_ms"] is not None:
            data[key]["state_prep_ms"].append(r["state_prep_ms"])

    engines = sorted({r["engine_name"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})

    headers = ["Engine", "Dimension", "Avg Search (ms)", "Avg State Prep (ms)", "Avg Total (ms)"]
    table_rows = []
    for engine in engines:
        for dim in dimensions:
            key = (engine, dim)
            if key not in data:
                continue
            d = data[key]
            state_prep = _fmt(_avg(d["state_prep_ms"])) if d.get("state_prep_ms") else "—"
            table_rows.append([
                f"`{engine}`",
                str(dim),
                _fmt(_avg(d["search_ms"])),
                state_prep,
                _fmt(_avg(d["total_ms"])),
            ])

    note = (
        "> Speed is shown **per engine** to observe how each scales with dimension.\n"
        "> Cross-engine speed comparison is not meaningful: the quantum engine runs on a classical\n"
        "> circuit simulator, so its wall-clock time reflects simulation overhead, not real quantum hardware latency.\n"
    )
    return "## Speed Scaling by Dimension (per engine)\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_shots_to_accuracy(rows: list[dict]) -> str:
    """Quantum-specific KPI: accuracy achieved at each shots value."""
    quantum_rows = [r for r in rows if r["state_prep_ms"] is not None and r["state_prep_ms"] > 0]
    if not quantum_rows:
        return ""

    by_shots: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in quantum_rows:
        params = r["parameters"] or {}
        shots = params.get("shots")
        if shots is None:
            continue
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        by_shots[shots]["accuracy"].append(r["accuracy"])
        by_shots[shots]["recall"].append(_recall(targets, top))
        by_shots[shots]["mrr"].append(_mrr(targets, top))

    if not by_shots:
        return ""

    headers = ["Shots", "Weighted Accuracy", "Recall@K", "MRR", "Runs"]
    table_rows = []
    for shots in sorted(by_shots):
        d = by_shots[shots]
        table_rows.append([
            str(shots),
            _pct(_avg(d["accuracy"])),
            _pct(_avg(d["recall"])),
            _fmt(_avg(d["mrr"]), 3),
            str(len(d["accuracy"])),
        ])

    note = (
        "> Shots = number of quantum circuit measurements per query.\n"
        "> On real hardware, fewer shots = lower cost. This table shows the minimum shots\n"
        "> needed to reach acceptable accuracy.\n"
    )
    return "## Quantum: Shots vs. Accuracy\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_head_to_head(rows: list[dict]) -> str:
    """Quality-only head-to-head across all (query, dimension) combinations."""
    engines = sorted({r["engine_name"] for r in rows})
    if len(engines) < 2:
        return ""

    index = {(r["query_id"], r["engine_name"], r["dimension"], _get_top_k(r)): r for r in rows}
    queries = sorted({r["query_id"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})
    top_k_vals = sorted({_get_top_k(r) for r in rows} - {0})

    headers = (
        ["Query", "Dim", "top_k"]
        + [f"`{e}` Accuracy" for e in engines]
        + [f"`{e}` Recall@K" for e in engines]
        + [f"`{e}` MRR" for e in engines]
    )
    table_rows = []
    for query in queries:
        for dim in dimensions:
            for k in top_k_vals:
                row_cells = [f"`{query}`", str(dim), str(k)]
                for engine in engines:
                    r = index.get((query, engine, dim, k))
                    row_cells.append(_pct(r["accuracy"]) if r else "—")
                for engine in engines:
                    r = index.get((query, engine, dim, k))
                    targets = (r["target_ids"] or []) if r else []
                    top = (r["top_ids"] or []) if r else []
                    row_cells.append(_pct(_recall(targets, top)) if r else "—")
                for engine in engines:
                    r = index.get((query, engine, dim, k))
                    targets = (r["target_ids"] or []) if r else []
                    top = (r["top_ids"] or []) if r else []
                    row_cells.append(_fmt(_mrr(targets, top), 3) if r else "—")
                table_rows.append(row_cells)

    return "## Head-to-Head Quality Comparison\n\n" + _md_table(headers, table_rows)


def _section_per_query(rows: list[dict]) -> str:
    queries = sorted({r["query_id"] for r in rows})
    engines = sorted({r["engine_name"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})
    index = {(r["query_id"], r["engine_name"], r["dimension"], _get_top_k(r)): r for r in rows}
    top_k_vals = sorted({_get_top_k(r) for r in rows} - {0})

    sections = ["## Per-Query Detail\n"]
    for query in queries:
        sections.append(f"### `{query}`\n")
        headers = ["Engine", "Dim", "top_k", "Weighted Acc", "Recall@K", "MRR", "Top Results"]
        table_rows = []
        for engine in engines:
            for dim in dimensions:
                for k in top_k_vals:
                    r = index.get((query, engine, dim, k))
                    if r is None:
                        continue
                    targets = r["target_ids"] or []
                    top = r["top_ids"] or []
                    table_rows.append([
                        f"`{engine}`",
                        str(dim),
                        str(k),
                        _pct(r["accuracy"]),
                        _pct(_recall(targets, top)),
                        _fmt(_mrr(targets, top), 3),
                        ", ".join(f"`{x}`" for x in top),
                    ])
        sections.append(_md_table(headers, table_rows))
        sections.append("")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Markdown benchmark report from the database.")
    parser.add_argument(
        "--out",
        default=str(BACKEND_ROOT / "docs" / "benchmark_report.md"),
        help="Output path for the report (default: backend/docs/benchmark_report.md)",
    )
    args = parser.parse_args()

    dsn = (
        f"postgresql://{os.getenv('DB_USER', 'qvs')}:{os.getenv('DB_PASSWORD', 'qvs')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '6432')}"
        f"/{os.getenv('DB_NAME', 'qvs_benchmarks')}"
    )

    rows = _fetch_rows(dsn)
    if not rows:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("# Benchmark Report\n\n_No results yet. Run `python3 scripts/run_benchmarks.py` first._\n")
        print(f"No results found — empty report written to {out_path}")
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sections = [
        "# Benchmark Report\n",
        "_Generated by `backend/scripts/generate_report.py`_\n",
        _section_overview(rows),
        "",
        _section_winner(rows),
        "",
        _section_kpi_summary(rows),
        "",
        _section_quality_by_dimension(rows),
        "",
        _section_quality_by_top_k(rows),
        "",
        _section_head_to_head(rows),
        "",
        _section_shots_to_accuracy(rows),
        "",
        _section_circuit_complexity(rows),
        "",
        _section_speed_scaling(rows),
        "",
        _section_per_query(rows),
    ]

    out_path.write_text("\n".join(sections))
    print(f"Report written to {out_path}")


if __name__ == "__main__":
    main()
