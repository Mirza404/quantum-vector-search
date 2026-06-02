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

## Architecture at a glance

```
text
  -> CLIP ViT-B/32
  -> truncate to 64/128/256 dimensions
  -> one of 7 active engines
  -> PostgreSQL + pgvector
  -> FastAPI + React
```

Engine-count convention: the active benchmark/live-search set has 7 engines
(3 classical, 4 quantum or hybrid). Stored benchmark results can show an 8th
engine ID, `hybrid_hnsw_swap_test_ibm`, because the IBM hardware validation is
run separately at dimension 2 with two candidates and 32 shots. Treat IBM as a
validation data point, not as part of the normal simulator sweep.

A proper diagram (`docs/architecture.png`) is on the figure punch list - see `report/STRUCTURE.md`.

## Documentation

| Doc | What's in it |
|---|---|
| [`docs/NOTES.md`](docs/NOTES.md) | Architecture, engineering principles, five-phase pipeline, DB schema |
| [`docs/THEORY.md`](docs/THEORY.md) | Cheat sheet: similarity metrics, CLIP, swap test, Grover, MRR, qubit counts |
| [`docs/ENGINES_GUIDE.md`](docs/ENGINES_GUIDE.md) | Every engine, its parameters, and what they trade off |
| [`docs/QUANTUM_INTUITION.md`](docs/QUANTUM_INTUITION.md) | Plain-language walk-through of the quantum bits |
| [`docs/QUANTUM_SEARCH_ANALYSIS.md`](docs/QUANTUM_SEARCH_ANALYSIS.md) | qRAM, scaling, the honest quantum picture |
| [`docs/RESEARCH_QUESTIONS.md`](docs/RESEARCH_QUESTIONS.md) | What we set out to measure |
| [`docs/BENCHMARK_KPIS.md`](docs/BENCHMARK_KPIS.md) | MRR, oracle calls, circuit depth - precise definitions |
| [`docs/FAQ.md`](docs/FAQ.md) | Questions the team kept hitting while building |
| [`docs/LEARNING_ROADMAP.md`](docs/LEARNING_ROADMAP.md) | If you want to learn the theory end-to-end |
| [`docs/midterm/`](docs/midterm/) | Midterm presentation HTML + speaker notes |
| [`report/`](report/) | LaTeX graduation-project report (build with `make` inside `report/`) |
| [`poster/`](poster/) | A0 portrait HTML poster (open `poster/index.html` in a browser) |

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
   The report is generated at `backend/reports/benchmark_report.md`.

## Database

All db commands run from the `db/` directory - see `db/Makefile` for the full list.

To share results: `make dump` from `db/`, then commit `db/seeds/seed.sql`.

## Adminer

Open **http://localhost:8080** after `make up`. Use `postgres` as the server (Docker service name), credentials from `.env`.

See `backend/README.md` for package layout, config, and advanced usage.
