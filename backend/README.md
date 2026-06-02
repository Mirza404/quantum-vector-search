# Backend

FastAPI backend and benchmark harness for the classical, quantum, and hybrid search engines.

The PostgreSQL database must be running first. `DatabaseStorage` connects on startup, so indexing, benchmarks, report generation, and the API will error if the database from [`../db`](../db/README.md) is not available.

## Setup

```bash
cd db
cp .env.example .env
make up
make migrate
make seed

cd ../backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The default database settings in `backend/.env.example` match `db/.env.example`: host `localhost`, port `6432`, database `qvs_benchmarks`, user `qvs`, password `qvs`.

## Package Structure

```text
src/
|-- benchmark/   # result models, benchmark query loading, DatabaseStorage
|-- engines/     # SearchEngineStrategy base and engine implementations
|-- pipeline/    # CLIPEmbeddingModel and embedding interfaces
`-- repository/  # DirectoryDataLoader and dataset interfaces
```

## Dataset And Indexing

`config/dataset.yaml` controls how many Flickr30k images are imported. The committed seed already contains the project benchmark data, but a fresh run can rebuild it:

```bash
python3 scripts/import_dataset.py
python3 scripts/index_dataset.py
```

`import_dataset.py` downloads the configured Flickr30k subset into `data/images/` and writes `data/ground_truth.jsonc`. `index_dataset.py` encodes the images with CLIP and stores vectors in PostgreSQL.

## Benchmark Sweep

`config/benchmarks.yaml` selects the active engines, dimensions, shot counts, layer values, and `top_k`. The normal sweep uses seven active engines: three classical and four quantum or hybrid. The IBM engine ID is kept out of the default sweep and is used only by the separate hardware validation.

Run the configured sweep from `backend/`:

```bash
python3 scripts/run_benchmarks.py
```

Useful one-off overrides:

```bash
python3 scripts/run_benchmarks.py --dimensions 64 128
python3 scripts/run_benchmarks.py --shots-values 512 2048
python3 scripts/run_benchmarks.py --device cpu --batch-size 16
```

Existing rows are skipped by run key, so rerunning the sweep fills missing combinations without duplicating completed ones.

## Generate The Benchmark Report

After the database contains benchmark rows:

```bash
python3 scripts/generate_report.py
```

The output is [`reports/benchmark_report.md`](reports/benchmark_report.md). It is the source of truth for the report's numerical claims.

## API

With the database running and dependencies installed:

```bash
uvicorn app.main:app --reload
```

Live search settings come from `config/benchmarks.yaml` under `live_search` and can be overridden with `SEARCH_DIMENSION`, `SEARCH_SHOTS`, `SEARCH_LAYERS`, and `SEARCH_TOP_K`.

## IBM Hardware Validation

IBM hardware runs are intentionally separate from the default benchmark sweep. Set `IBM_QUANTUM_TOKEN` in `backend/.env` and keep `IBM_QUANTUM_ALLOW_PAID=false` unless paid runtime use is intentional.

```bash
python3 scripts/run_ibm_smoke.py
python3 scripts/run_ibm_validation.py
```

The validation script writes `hybrid_hnsw_swap_test_ibm` rows for the tiny hardware run: dimension 2, two candidates, 32 shots, 20 queries.
