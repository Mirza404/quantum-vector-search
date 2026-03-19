# Quantum Vector Search

Compares classical and quantum-inspired vector search engines for cross-modal similarity search (text to image). Uses CLIP embeddings and benchmarks four engines against the same dataset. React dashboard planned for a future phase.

## Quick Start

**Prerequisites:** Docker + Compose v2, Python 3.12+

1. **Database**
   ```bash
   make db-up
   make db-seed
   ```

2. **Backend**
   ```bash
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e . --extra-index-url https://download.pytorch.org/whl/cpu
   cp .env.example .env
   ```

3. **Run benchmarks**
   ```bash
   python3 scripts/run_benchmarks.py
   ```

4. **Generate report**
   ```bash
   python3 scripts/generate_report.py
   ```

## Database

| Command | What it does |
|---|---|
| `make db-up` | Start Postgres |
| `make db-migrate` | Apply pending migrations |
| `make db-seed` | Reset DB to seed state |
| `make db-rollback N=2` | Roll back migrations above N |
| `make db-dump` | Dump all data to `db/seeds/` |
| `make db-reset` | Wipe volume and start fresh |

To share results, run `make db-dump` and commit `db/seeds/benchmark_results.sql`.

See `backend/README.md` for package layout, config, and advanced usage.
