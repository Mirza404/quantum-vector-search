# Backend README

Python benchmarking harness that exercises classical and quantum-inspired search engines against a tiny sample dataset. Everything runs locally; a PostgreSQL container stores the benchmark rows so teammates can share results.

## 1. Prerequisites
- Docker + Docker Compose v2
- Python 3.12+
- `pip` for dependency management

## 2. Spin Up PostgreSQL
```bash
cd db
docker compose up -d
docker exec -i qvs-postgres psql -U qvs -d qvs_benchmarks < db/schema.sql
docker exec -i qvs-postgres psql -U qvs -d qvs_benchmarks < db/data.sql  # optional seed
```
The container starts bare — tables are not created automatically. `schema.sql` drops and recreates `benchmark_results`; `data.sql` seeds it from a prior export. The DSN defaults to `postgresql://qvs:qvs@localhost:6432/qvs_benchmarks`.

## 3. Install Dependencies & Configure Env
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e . --extra-index-url https://download.pytorch.org/whl/cpu
cp .env.example .env  # sets QVS_BENCHMARK_DSN
```
`QVS_BENCHMARK_DSN` is read automatically by `DatabaseStorage`; override it if you run PostgreSQL elsewhere.

## 4. Configure & Run Benchmarks
1. Edit `backend/config/benchmarks.yaml` to toggle engines, dimensions, and query IDs. Comment out entries you do not want for the next run.
2. Run the harness from the backend root (it patches `sys.path` automatically):
   ```bash
   python3 scripts/run_benchmarks.py
   ```
Results are written to the database. To export them as a Markdown report:
```bash
python3 scripts/generate_report.py
```
This writes `backend/docs/benchmark_report.md` with quality KPIs (weighted accuracy, Recall@K, MRR), quantum circuit complexity metrics, and per-query breakdowns.

## 5. Package Structure
```
src/qvs/
├── benchmark/   # benchmark dataclasses + storage strategies
├── engines/     # SearchEngineStrategy base + mock/vector/quantum engines
├── pipeline/    # Embedding interfaces, CLIP wrapper, deterministic mock
└── repository/  # Dataset abstractions (LocalCSV loader today)
```

Future phases will introduce a FastAPI API and a React dashboard that consumes benchmark history.
