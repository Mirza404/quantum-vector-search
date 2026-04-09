# Benchmark KPI Definitions

All metrics are measured **per query**, not per benchmark run. One DB row = one query = one set of measurements. This is how `run_benchmarks.py` and `generate_report.py` work.

---

## Unified Metrics (all engines)

These apply to every engine — classical, simulator, IBM — with no exceptions.

### MRR (Mean Reciprocal Rank) — Primary KPI

Measures how high the correct result ranks: 1.0 = first, 0.5 = second, 0.33 = third. Hardware-independent, directly comparable across all engines.

- Implemented in `_mrr()` in both `run_benchmarks.py` and `generate_report.py`
- Computed from `target_ids` and `top_ids` columns
- The harness ranks ALL dataset images (no top-K cutoff) to capture the true rank

### Time per Query

Tracked as `search_ms`, `state_prep_ms`, `total_ms` in the DB. **Never compared across engines.**

| Engine | Track in DB? | Report as KPI? | What it measures |
|---|---|---|---|
| `brute_force_cosine` | Yes | Yes | Real classical performance |
| `faiss_flat` | Yes | Yes | Real classical performance |
| `qiskit_swaptest` simulator | Yes | No | CPU simulation overhead |
| `qiskit_grover` simulator | Yes | No | CPU simulation overhead |
| `qiskit_swaptest` IBM | Yes (execution time only) | No | Real hardware time, but O(N) so uninteresting for speed |
| `qiskit_grover` IBM | Yes (execution time only) | Supporting data | Real quantum hardware time -- notable but not cross-engine comparable |

- Classical wall-clock is reported per engine and plotted vs N -- the scaling curve is real and valid
- Simulator wall-clock is kept in the DB as operational data only (tells you how long a benchmark run takes) and **never appears in a report graph**
- IBM total wall-clock is never recorded -- queue wait and network latency dominate and are irrelevant
- IBM circuit execution time comes from job metadata only and requires Qiskit Runtime Session mode for per-query granularity

### Operation Count vs N — The Cross-Engine Scaling KPI

This is the **only valid cross-engine comparison for speed**.

| Engine | Operations per query | Complexity |
|---|---|---|
| `brute_force_cosine` | N comparisons | O(N) |
| `faiss_flat_l2` | N comparisons | O(N) |
| `quantum_mock_sampler` | N comparisons | O(N) |
| `qiskit_swap_test` | N circuit executions | O(N) |
| `qiskit_grover` | floor(pi * sqrt(N) / 4) oracle calls | O(sqrt(N)) |

Stored in `benchmark_results.oracle_calls`. Derivable from `engine_name` and `dataset_size` — no runtime instrumentation needed.

Plotted together against dataset size, this shows the O(N) vs O(sqrt(N)) scaling difference. The x-axis is dataset size, the y-axis is operations. The two curves diverge as N grows. **That divergence is the entire point of quantum search.**

---

## Quantum-Only Metrics

### Shots-to-Quality

MRR at each shots value. Shows the minimum measurement budget needed to reach acceptable accuracy. Useful for understanding the cost of running on real hardware.

- Reported in the "Quantum: Shots vs. Quality" section of `generate_report.py`
- Controlled by `shots_values` in `benchmarks.yaml`

### Circuit Depth / Qubit Count

Hardware-agnostic cost proxies broken down by engine and dataset size.

- **Circuit depth** = number of sequential gate layers; deeper circuits are more susceptible to decoherence on real hardware
- **Qubit count** = number of qubits required; more qubits = harder to allocate on near-term devices
- Stored in `benchmark_results.circuit_depth` and `benchmark_results.num_qubits`
- Reported in the "Quantum Circuit Complexity" section of `generate_report.py`

---

## What Is NOT a KPI

### Cross-engine wall-clock comparison
Not valid. Classical runs locally, IBM is accessed over HTTP with queue overhead, simulator reflects CPU simulation cost. These are different environments and the numbers are not comparable.

### Simulator wall-clock vs N scaling
Not valid as a quantum KPI. The curve shows how expensive it is to *simulate* quantum circuits on a classical CPU, which gets worse than linear. This would make quantum look slower than classical for the wrong reasons.

### IBM total wall-clock
Not valid. Queue wait on free tier can be hours and dominates the number entirely.

---

## Database Schema

The `benchmark_results` table stores all metrics. Key columns for KPIs:

| Column | Type | Purpose |
|---|---|---|
| `target_ids` | JSONB | Ground truth — correct image IDs for MRR computation |
| `top_ids` | JSONB | Ranked search results |
| `search_ms` | DOUBLE PRECISION | Search step wall-clock (per-engine only) |
| `state_prep_ms` | DOUBLE PRECISION | State preparation wall-clock (quantum only) |
| `total_ms` | DOUBLE PRECISION | Total wall-clock (per-engine only) |
| `dataset_size` | INTEGER | Number of vectors searched |
| `oracle_calls` | INTEGER | Operations per query (cross-engine scaling KPI) |
| `circuit_depth` | INTEGER | Sequential gate layers (quantum only) |
| `num_qubits` | INTEGER | Qubits required (quantum only) |

Unique constraint: `(query_id, engine_name, dimension, shots, layers)` — re-running overwrites; new parameter combinations append.

---

## Report Sections in generate_report.py

| Section | KPI | Cross-engine? |
|---|---|---|
| Results Summary | MRR | Yes |
| Quality KPIs by Engine | MRR | Yes |
| Quality by Dimension | MRR | Yes |
| Operation Count Scaling | oracle_calls vs N | Yes |
| Head-to-Head Comparison | MRR per query | Yes |
| Shots vs. Quality | MRR at each shots value | Quantum only |
| Circuit Complexity | depth, qubits | Quantum only |
| Speed Scaling by Dimension | ms vs dimension | Per-engine only |
| Per-Query Detail | MRR, top results | Yes |
