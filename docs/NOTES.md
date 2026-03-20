# Quantum-Enhanced Multi-Modal Vector Search: A Hybrid Database Web App

## Problem Statement & Project Overview
Modern applications often require similarity search on large amounts of cross-modal data (for example: searching images using text description). Classic vector and embedding methods provide sufficient solutions, however new quantum computing techniques could offer performance and accuracy improvement. In this project, we aim to bridge the gap in existing research by directly comparing classical vector search methods with emerging quantum-based techniques.

We plan to create a hybrid web application that performs cross-modal search using both classical and quantum engines. Results and metrics will be displayed in a web-based dashboard. Since current quantum hardware and simulators operate differently than classical processors, our primary goal is not to compare raw execution speed — this is meaningless when quantum runs on a classical simulator. Instead, we evaluate accuracy trade-offs, quantum circuit resource cost (circuit depth, qubit count), and scaling behaviour to determine when, or if, quantum processing offers theoretical or practical benefits at a small scale.

## Objectives & Expected Deliverables
**Objectives:**
* Develop parallel search engines: classical vector and quantum, so they can be compared side-by-side.
* Build a shared embedding pipeline that converts text and images into a single space using CLIP.
* Design and develop an interactive web interface that allows users to submit text queries and view matching images.
* Provide analysis about results and draw conclusions based on returned metrics.

**Expected Deliverables:**
* Fully functional web application that demonstrates cross-modal search.
* Experimental dataset and evaluation pipeline.
* Comparison between classical and quantum methods.
* Conclusion about practical benefits and limitations of quantum vector search.

## Core Engineering Philosophy
* **Modular Monolith:** Everything lives in one repository with strictly isolated folders. The web server remains agnostic to quantum math.
* **API-First Design:** Core logic runs behind FastAPI. Hooking up the React frontend requires zero backend changes.
* **No UI in MVP:** The MVP is driven 100% by an automated Python benchmarking script.
* **Strategy Pattern:** Data loading, search engines, and storage use interfaces (base classes) to allow swapping underlying technologies.

---

## System Architecture & Implementation Phases

### Phase 1: The Repository Layer (Data Management) ✅
Responsible for fetching the experimental dataset.
* **Component:** `BaseDataLoader` interface with a `get_dataset()` method.
* **Implementation:** `LocalCSVDataLoader` — reads local images and a CSV mapping text to image paths from `backend/data/sample_dataset/`.
* **Rule:** No user uploads for the MVP. A stable, controlled baseline is required for reproducible empirical results.

### Phase 2: The On-Demand Embedding Pipeline ✅
CLIP-based pipeline converts cross-modal data (text/images) into a shared embedding space whenever a benchmark run starts. There is no preprocessing or cache — the harness loads the dataset, encodes images and text with `CLIPEmbeddingModel`, and reuses those vectors for the duration of the run.
* **Implementations:** `CLIPEmbeddingModel` (real CLIP, ViT-B/32) and `MockCLIPEmbeddingGenerator` for lightweight tests. Both live behind the `EmbeddingGenerator` interface.

### Phase 3: The Modular Search Engines ✅
Four engines, all implementing `SearchEngineStrategy` with `build_index()` and `search()`:

| Engine | Class | Type |
|---|---|---|
| `brute_force_cosine` | `BruteForceCosineEngine` | Deterministic cosine similarity, brute-force NumPy. Fast baseline. |
| `faiss_flat_l2` | `FaissFlatEngine` | Real FAISS `IndexFlatL2`. Production-grade classical search. |
| `quantum_mock_sampler` | `QuantumMockEngine` | Cosine + configurable noise simulating quantum measurement error. No real circuits. |
| `qiskit_swap_test` | `QiskitSwapTestEngine` | Real Qiskit circuit running a swap test on AerSimulator. |

Active engines are controlled by `backend/config/benchmarks.yaml` — comment out entries to skip without code changes.

### Phase 4: Database Benchmarking Storage ✅
All benchmark results write directly to PostgreSQL. No CSV files.

**Infrastructure (in `db/`, outside Python backend):**
* `docker-compose.yml` — starts `pgvector/pgvector:pg16` + Adminer web UI (http://localhost:8080).
* `migrations/up/` — numbered SQL files (`1_initial_schema.sql`, …) applied in order by `migrate.sh up`. Filenames are recorded in `schema_migrations` so each runs exactly once.
* `migrations/down/` — paired rollback scripts with the same filenames. Run in reverse by `migrate.sh down [N]`.
* `seeds/seed.sql` — source of truth for all table data. `make seed` resets the DB to this exact state. Updated by `make dump` and committed so teammates get the latest data on `git pull`.
* `migrate.sh` — `up` applies pending migrations; `down [N]` rolls back everything above N.
* `seed.sh` — smart seed: rolls back any migrations above the seed's recorded state, loads the seed, then migrates forward. Safe whether the DB is behind or ahead.
* `dump.sh` — dumps all tables into `db/seeds/`; run via `make dump`.

**Contributor workflow (from `db/`):**
```bash
make up        # start Postgres, wait for healthcheck
make seed      # rolls back if ahead, loads seed, migrates forward
```
To share new results: `make dump` from `db/`, commit `db/seeds/seed.sql`.

Adding a new migration: create paired `db/migrations/up/N_name.sql` and `db/migrations/down/N_name.sql`, then run `make migrate`.

**`benchmark_results` table columns:**
`query_id`, `engine_name`, `dimension`, `target_ids`, `top_ids`, `accuracy`, `state_prep_ms`, `search_ms`, `total_ms`, `parameters`, `dataset_size`, `circuit_depth`, `num_qubits`

**`image_vectors` table:** Stores persistent CLIP embeddings for all dataset images.
`id` (TEXT PRIMARY KEY), `embedding` (vector(512) — CLIP ViT-B/32 output), `recorded_at`
Indexed with HNSW cosine ops (`vector_cosine_ops`) for nearest-neighbour search.

**Report generation:** `backend/scripts/generate_report.py` queries the DB and writes `backend/docs/benchmark_report.md`.

### Phase 5: API & React Dashboard (in progress)
* **Backend (FastAPI):** `GET /search?q=<text>` encodes the query with CLIP, runs a cosine nearest-neighbour query against `image_vectors`, and returns the top-K image IDs. `GET /api/benchmarks` retrieves historical results from the DB.
* **Frontend (React):** Text search bar returning matching images side-by-side. Benchmark dashboard charting accuracy vs. dimensions, circuit complexity, shots-to-accuracy.
* **Vector storage (implemented):** CLIP embeddings for all dataset images are stored persistently in `image_vectors` via the **pgvector** extension (a drop-in replacement for the standard Postgres image — same DSN, same Docker Compose file). Embeddings are upserted automatically on every benchmark run — no separate step required. What remains is the FastAPI search endpoint and wiring the React search box to it.

---

## Configuration-Driven Benchmarking

`backend/config/benchmarks.yaml` controls every benchmark run:
* **List sections:** `engines`, `dimensions`, `queries` — comment out entries to skip.
* **Scalar values:** `top_k` (results per query), `shots` (quantum measurement count), `layers` (variational circuit depth).

CLI flags (`--top-k`, `--shots`, `--layers`) override the YAML values for one-off runs.

Run from the backend root:
```bash
cd backend && python3 scripts/run_benchmarks.py
```

---

## KPIs & Metrics

Cross-engine comparisons use **quality metrics only**. Cross-engine speed comparison is intentionally excluded — the quantum engine runs on a classical simulator, so wall-clock time reflects simulation overhead, not real quantum hardware latency.

**Quality KPIs (cross-engine):**
| Metric | Description |
|---|---|
| Weighted Accuracy | Positional score: 1.0 (rank 1) / 0.66 (rank 2) / 0.33 (rank 3). NDCG-lite. |
| Recall@K | Did the relevant item appear anywhere in top-K? |
| MRR | Mean Reciprocal Rank — where did the first relevant result land? |

**Quantum-specific KPIs:**
| Metric | Description |
|---|---|
| Circuit depth | Sequential gate layers — proxy for decoherence risk on real hardware. |
| Num qubits | Qubits required — proxy for hardware allocation cost. |
| Shots vs. accuracy | Minimum measurement budget to reach acceptable accuracy. |

**Speed (per-engine only):** Valid to compare dim=64 vs dim=128 *within* the same engine to observe scaling. Not valid across engines.
