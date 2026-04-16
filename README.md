# Quantum Vector Search

## What is this?

You type `"a dog on a beach"`. The app finds matching images - even though no one labelled them
with that phrase. That is cross-modal search: searching one type of data (text) and getting
results in another type (images).

The core question this project answers: **does quantum similarity search work, how accurate is
it, and what does it cost in quantum resources?** We run the same search through multiple
engines - classical (standard CPU math) and quantum (circuits on a simulated or real quantum
chip) - and measure accuracy (MRR) alongside quantum resource cost (qubits, circuit depth,
measurement shots).

**We are not claiming quantum is faster.** Classical computers have already won that race for
now. The point is to establish the baseline - built now, while quantum hardware is still too
limited to run it at scale, so the benchmarking framework and resource cost model are ready
when the hardware catches up.

For the full theory, design decisions, and Q&A see the [`docs/`](docs/) folder.

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
   pip install -r requirements.txt
   ```

3. **Index images** (one-time - encodes images with CLIP and stores vectors in Postgres)
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

All db commands run from the `db/` directory - see `db/Makefile` for the full list.

To share results: `make dump` from `db/`, then commit `db/seeds/seed.sql`.

## Adminer

Open **http://localhost:8080** after `make up`. Use `postgres` as the server (Docker service name), credentials from `.env`.

See `backend/README.md` for package layout, config, and advanced usage.
