#!/usr/bin/env python3
"""Generate a Markdown benchmark report from the database.

Usage (from repo root):
    python3 backend/scripts/generate_report.py
    python3 backend/scripts/generate_report.py --out docs/report.md

KPIs
----
Cross-engine comparisons focus solely on result quality:
  - MRR                : 1 / rank of the first relevant result

Speed (ms) is reported *per engine* only to show how each engine scales with
dimension.  Cross-engine wall-clock comparisons are intentionally omitted:
the quantum engine runs on a classical simulator, so its timing reflects
circuit-simulation overhead rather than real quantum hardware latency.

Cross-engine scaling comparison:
  - Operation count    : Classical engines use N comparisons per query.
                         Grover uses floor(π√N/4) oracle calls per query.
                         This is the only valid cross-engine "speed" metric.

Quantum-specific KPI:
  - Shots-to-quality   : MRR at each shots value, showing the minimum
                         measurement budget needed to reach a target.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from benchmark.db_storage import _bootstrap_env  # noqa: E402

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
                    state_prep_ms, search_ms, total_ms,
                    parameters, dataset_size, circuit_depth, num_qubits,
                    oracle_calls
                FROM benchmark_results
                ORDER BY engine_name, dimension, query_id
            """)
            return cur.fetchall()


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


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
    lines = [
        "## Overview\n",
        "| Metric | Value |",
        "|---|---|",
        f"| Total runs | {len(rows)} |",
        f"| Engines | {', '.join(f'`{e}`' for e in engines)} |",
        f"| Dimensions | {', '.join(str(d) for d in dimensions)} |",
        f"| Queries | {', '.join(f'`{q}`' for q in queries)} |",
    ]
    return "\n".join(lines)


def _section_winner(rows: list[dict]) -> str:
    """Top-line summary: MRR for each engine side by side, with winner."""
    by_engine: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        e = r["engine_name"]
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        by_engine[e].append(_mrr(targets, top))

    engines = sorted(by_engine)
    scores = {e: _avg(by_engine[e]) for e in engines}
    best_val = max(scores.values())
    winners = [e for e, s in scores.items() if s == best_val]
    best_label = "Tie" if len(winners) == len(engines) else ", ".join(f"`{e}`" for e in sorted(winners))

    headers = ["KPI"] + [f"`{e}`" for e in engines] + ["Best"]
    table_rows = [
        ["MRR"] + [_fmt(scores[e], 3) for e in engines] + [best_label],
    ]
    return "## Results Summary\n\n" + _md_table(headers, table_rows)


def _section_kpi_summary(rows: list[dict]) -> str:
    """Cross-engine quality KPI: MRR."""
    by_engine: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        e = r["engine_name"]
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        by_engine[e].append(_mrr(targets, top))

    headers = ["Engine", "MRR", "Runs"]
    table_rows = []
    for engine in sorted(by_engine):
        mrr_vals = by_engine[engine]
        table_rows.append([
            f"`{engine}`",
            _fmt(_avg(mrr_vals), 3),
            str(len(mrr_vals)),
        ])

    note = (
        "> **MRR** (Mean Reciprocal Rank) - 1 / rank of the first correct result, averaged over all queries.\n"
        "> Higher = the correct image appears closer to position 1.\n"
    )
    return "## Quality KPIs by Engine\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_quality_by_dimension(rows: list[dict]) -> str:
    """MRR broken down by engine and dimension."""
    data: dict[tuple[str, int], list[float]] = defaultdict(list)
    for r in rows:
        key = (r["engine_name"], r["dimension"])
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        data[key].append(_mrr(targets, top))

    engines = sorted({r["engine_name"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})

    headers = ["Engine", "Dimension", "MRR"]
    table_rows = []
    for engine in engines:
        for dim in dimensions:
            key = (engine, dim)
            if key not in data:
                continue
            table_rows.append([
                f"`{engine}`",
                str(dim),
                _fmt(_avg(data[key]), 3),
            ])

    note = "> Quality metric only. Speed is excluded from cross-engine comparisons - see per-engine scaling below.\n"
    return "## Quality by Dimension\n\n" + note + "\n" + _md_table(headers, table_rows)


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
        # These are constant per (engine, dim, dataset_size) - just take the first value.
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
            state_prep = _fmt(_avg(d["state_prep_ms"])) if d.get("state_prep_ms") else "-"
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


def _section_shots_to_quality(rows: list[dict]) -> str:
    """Quantum-specific KPI: MRR at each shots value."""
    quantum_rows = [r for r in rows if r["state_prep_ms"] is not None and r["state_prep_ms"] > 0]
    if not quantum_rows:
        return ""

    by_shots: dict[int, list[float]] = defaultdict(list)
    for r in quantum_rows:
        params = r["parameters"] or {}
        shots = params.get("shots")
        if shots is None:
            continue
        targets = r["target_ids"] or []
        top = r["top_ids"] or []
        by_shots[shots].append(_mrr(targets, top))

    if not by_shots:
        return ""

    headers = ["Shots", "MRR", "Runs"]
    table_rows = []
    for shots in sorted(by_shots):
        mrr_vals = by_shots[shots]
        table_rows.append([
            str(shots),
            _fmt(_avg(mrr_vals), 3),
            str(len(mrr_vals)),
        ])

    note = (
        "> Shots = number of quantum circuit measurements per query.\n"
        "> On real hardware, fewer shots = lower cost. This table shows the minimum shots\n"
        "> needed to reach acceptable MRR.\n"
    )
    return "## Quantum: Shots vs. Quality\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_operation_count_scaling(rows: list[dict]) -> str:
    """Cross-engine scaling comparison: operation count vs dataset size.

    Classical engines use N comparisons.  Grover uses floor(π√N/4) oracle
    calls.  This is the only valid cross-engine "speed" metric because it is
    hardware-independent and directly captures the O(N) vs O(√N) difference.
    """
    # Group by (engine, dataset_size) - average oracle_calls (should be constant per group)
    data: dict[tuple[str, int], list[int]] = defaultdict(list)
    for r in rows:
        oc = r.get("oracle_calls")
        if oc is None:
            continue
        key = (r["engine_name"], r["dataset_size"])
        data[key].append(oc)

    if not data:
        return ""

    engines = sorted({e for e, _ in data})
    dataset_sizes = sorted({ds for _, ds in data})

    headers = ["Engine", "Dataset Size (N)", "Operations per Query", "Complexity Class"]
    table_rows = []
    for engine in engines:
        for ds in dataset_sizes:
            key = (engine, ds)
            if key not in data:
                continue
            ops = data[key][0]
            complexity = "O(√N)" if engine == "qiskit_grover" else "O(N)"
            table_rows.append([
                f"`{engine}`",
                str(ds),
                str(ops),
                complexity,
            ])

    note = (
        "> **Operation count** is the cross-engine scaling KPI.\n"
        "> Classical engines perform N comparisons per query (linear scan).\n"
        "> Grover's algorithm uses floor(π√N/4) oracle calls per query.\n"
        "> This comparison is hardware-independent - it measures algorithmic efficiency,\n"
        "> not wall-clock time. The divergence between O(N) and O(√N) as N grows is the\n"
        "> entire argument for quantum search at scale.\n"
    )
    return "## Operation Count Scaling (O(N) vs O(√N))\n\n" + note + "\n" + _md_table(headers, table_rows)


def _section_head_to_head(rows: list[dict]) -> str:
    """MRR head-to-head across all (query, dimension) combinations."""
    engines = sorted({r["engine_name"] for r in rows})
    if len(engines) < 2:
        return ""

    index = {(r["query_id"], r["engine_name"], r["dimension"]): r for r in rows}
    queries = sorted({r["query_id"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})

    headers = ["Query", "Dim"] + [f"`{e}` MRR" for e in engines]
    table_rows = []
    for query in queries:
        for dim in dimensions:
            row_cells = [f"`{query}`", str(dim)]
            for engine in engines:
                r = index.get((query, engine, dim))
                targets = (r["target_ids"] or []) if r else []
                top = (r["top_ids"] or []) if r else []
                row_cells.append(_fmt(_mrr(targets, top), 3) if r else "-")
            table_rows.append(row_cells)

    return "## Head-to-Head Quality Comparison\n\n" + _md_table(headers, table_rows)


def _section_per_query(rows: list[dict]) -> str:
    queries = sorted({r["query_id"] for r in rows})
    engines = sorted({r["engine_name"] for r in rows})
    dimensions = sorted({r["dimension"] for r in rows})
    index = {(r["query_id"], r["engine_name"], r["dimension"]): r for r in rows}

    sections = ["## Per-Query Detail\n"]
    for query in queries:
        sections.append(f"### `{query}`\n")
        headers = ["Engine", "Dim", "MRR", "Top Results"]
        table_rows = []
        for engine in engines:
            for dim in dimensions:
                r = index.get((query, engine, dim))
                if r is None:
                    continue
                targets = r["target_ids"] or []
                top = r["top_ids"] or []
                table_rows.append([
                    f"`{engine}`",
                    str(dim),
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
        print(f"No results found - empty report written to {out_path}")
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
        _section_operation_count_scaling(rows),
        "",
        _section_head_to_head(rows),
        "",
        _section_shots_to_quality(rows),
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
