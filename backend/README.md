# Backend README

Python benchmarking harness that exercises classical and quantum-inspired search engines against a tiny sample dataset. Everything runs locally; a PostgreSQL container stores the benchmark rows so teammates can share results.

## 1. Prerequisites
- Docker + Docker Compose v2
- Python 3.12+
- `uv` (or `pip`) for dependency management

## 2. Spin Up PostgreSQL
```bash
cd db
docker compose up -d
```
The compose file mounts `schema.sql` and `data.sql`. `schema.sql` creates `benchmark_results`; `data.sql` is optional and holds exported rows. The DSN defaults to `postgresql://qvs:qvs@localhost:6432/qvs_benchmarks`.

## 3. Install Dependencies & Configure Env
```bash
cd backend
uv pip install -e .
cp .env.example .env  # sets QVS_BENCHMARK_DSN
```
`QVS_BENCHMARK_DSN` is read automatically by `DatabaseStorage`; override it if you run PostgreSQL elsewhere.

## 4. Configure & Run Benchmarks
1. Edit `backend/config/benchmarks.yaml` to toggle engines, dimensions, and query IDs. Comment out entries you do not want for the next run.
2. Run the harness from the backend root (it patches `sys.path` automatically):
   ```bash
   python3 scripts/run_benchmarks.py --top-k 3
   ```
Results are appended to the database only; there is no CSV/Markdown output in the new design.

## 5. Package Structure
```
src/qvs/
├── benchmark/   # benchmark dataclasses + storage strategies
├── engines/     # SearchEngineStrategy base + mock/vector/quantum engines
├── pipeline/    # Embedding interfaces, CLIP wrapper, deterministic mock
└── repository/  # Dataset abstractions (LocalCSV loader today)
```

Future phases will introduce FAISS/Qiskit engines, a FastAPI surface, and the React dashboard that consumes benchmark history.
