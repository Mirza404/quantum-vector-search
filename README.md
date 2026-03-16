# Quantum Vector Search (Prototype)

Hybrid research sandbox that compares classical vector search with emerging quantum-inspired engines. The code lives entirely in this repo: a Python benchmarking backend (`backend/`) today, plus a React dashboard that will consume the benchmark API in a future phase.

## Project Areas
- `backend/` – deterministic benchmarking harness, sample dataset, and quantum/classical mock engines. See `backend/README.md` for the full walkthrough.
- React dashboard (coming soon) – will visualize the database of benchmark runs once the API layer is built.

## Quick Start
1. **Start the database**
   ```bash
   cd db
   docker compose up -d
   ```
2. **Install backend dependencies**
   ```bash
   cd backend
   uv pip install -e .
   cp .env.example .env  # contains QVS_BENCHMARK_DSN
   ```
3. **Run benchmarks (configuration-driven)**
   ```bash
   cd backend
   python3 scripts/run_benchmarks.py
   ```
   The harness reads `backend/config/benchmarks.yaml` to decide which engines, dimensions, and queries to execute and writes all results to PostgreSQL.

Need deeper context, package layout, or tuning instructions? Continue in `backend/README.md`.
