# Quantum Vector Search (Prototype)

Hybrid research sandbox that compares classical vector search with emerging quantum-inspired engines. The code lives entirely in this repo: a Python benchmarking backend (`backend/`) today, plus a React dashboard that will consume the benchmark API in a future phase.

## Project Areas
- `backend/` – benchmarking harness with four search engines (vector mock, FAISS, quantum mock, Qiskit swap-test), sample dataset, and a report generator. See `backend/README.md` for the full walkthrough.
- React dashboard (coming soon) – will visualize the database of benchmark runs once the API layer is built.

## Quick Start
1. **Start the database**
   ```bash
   cd db
   docker compose up -d
   ```
   This only starts a bare Postgres instance — no tables or data are created automatically.

2. **Init tables**
   ```bash
   docker exec -i qvs-postgres psql -U qvs -d qvs_benchmarks < db/schema.sql
   ```

3. **Seed data**
   ```bash
   docker exec -i qvs-postgres psql -U qvs -d qvs_benchmarks < db/data.sql
   ```

4. **View the database (optional)**
   Adminer starts alongside Postgres. Open **http://localhost:8080** and log in with:
   - System: `PostgreSQL`, Server: `postgres`, Username: `qvs`, Password: `qvs`, Database: `qvs_benchmarks`

5. **Install backend dependencies**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e . --extra-index-url https://download.pytorch.org/whl/cpu
   cp .env.example .env  # contains QVS_BENCHMARK_DSN
   ```

6. **Run benchmarks (configuration-driven)**
   ```bash
   cd backend
   python3 backend/scripts/run_benchmarks.py
   ```
   The harness reads `backend/config/benchmarks.yaml` to decide which engines, dimensions, and queries to execute and writes all results to PostgreSQL.

### Generating a benchmark report

To export all results from the DB into a Markdown report at `docs/benchmark_report.md`:
```bash
python3 backend/scripts/generate_report.py
```
The report is written to `backend/docs/benchmark_report.md` and includes an accuracy/speed summary per engine, a breakdown by dimension, and a head-to-head comparison table across all queries.

### Sharing benchmark data with the team

To export your local results into `db/data.sql` so teammates can seed from them:
```bash
bash db/dump.sh
```
This uses `pg_dump` inside the running container — no local Postgres tools needed.

Need deeper context, package layout, or tuning instructions? Continue in `backend/README.md`.
