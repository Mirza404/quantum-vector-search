# Quantum Vector Search

Compares classical and quantum-inspired vector search engines for cross-modal similarity search (text to image). Uses CLIP embeddings and benchmarks four engines against the same dataset. React dashboard planned for a future phase.

## Quick Start

**Prerequisites:** Docker + Compose v2, Python 3.12+

1. **Database**
   ```bash
   cd db
   cp .env.example .env
   make up
   make seed
   ```

2. **Backend**
   ```bash
   cd backend
   cp .env.example .env
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e . --extra-index-url https://download.pytorch.org/whl/cpu
   ```

3. **Index images** (one-time — encodes images with CLIP and stores vectors in Postgres)
   ```bash
   python3 scripts/index_dataset.py
   ```

4. **Run benchmarks**
   ```bash
   python3 scripts/run_benchmarks.py
   ```

5. **Generate report**
   ```bash
   python3 scripts/generate_report.py
   ```

## Database

All db commands run from the `db/` directory.

| Command | What it does |
|---|---|
| `make up` | Start Postgres |
| `make migrate` | Apply pending migrations |
| `make seed` | Reset DB to seed state |
| `make rollback N=2` | Roll back migrations above N |
| `make dump` | Dump all data to `seeds/` |
| `make clean` | Truncate all data, keep schema and migrations |
| `make reset` | Wipe volume and start fresh |

To share results, run `make dump` from `db/` and commit `db/seeds/seed.sql`.

## Adminer

Open **http://localhost:8080** after `make up`. Use `postgres` as the server (Docker service name), credentials from `.env`.

See `backend/README.md` for package layout, config, and advanced usage.
