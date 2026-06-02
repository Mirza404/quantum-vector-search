# Quantum Vector Search

This BSc graduation project compares text-to-image vector search across seven active engines: three classical baselines (brute force, FAISS flat, FAISS HNSW) and four quantum or hybrid engines (swap test, Grover, Grover with quantum state preparation, and HNSW plus swap-test reranking). The project is an honest empirical investigation of accuracy and quantum resource cost, not a quantum-advantage claim.

## Repo Map

| Path | What is there |
|---|---|
| [`backend/`](backend/) | FastAPI app, CLIP indexing, benchmark scripts, engine implementations, generated benchmark report. |
| [`frontend/`](frontend/) | React interface for live side-by-side search and benchmark summaries. |
| [`db/`](db/) | PostgreSQL + pgvector Docker setup, migrations, and seed data. |
| [`docs/`](docs/) | Engineering notes, theory notes, engine guide, KPIs, and FAQ. |
| [`midterm/`](midterm/) | Midterm presentation HTML and speaker notes. |
| [`report/`](report/) | Final LaTeX graduation report and submission-named PDF. |
| [`poster/`](poster/) | HTML/CSS reference version of the A0 exhibition poster and poster assets. |

## Quickstart

Prerequisites: Docker with Compose v2, Python 3.12 or newer, and a shell that can run the provided scripts.

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

The database must be running before the backend scripts or API start. See [`db/README.md`](db/README.md) for database setup and [`backend/README.md`](backend/README.md) for indexing, benchmark, and report commands.

## Reproduce The Benchmarks

The benchmark flow is documented in [`backend/README.md`](backend/README.md). In short: start and seed the database from [`db/`](db/), install backend dependencies, index the dataset if needed, run `scripts/run_benchmarks.py`, then run `scripts/generate_report.py`. The generated source of truth is [`backend/reports/benchmark_report.md`](backend/reports/benchmark_report.md).

## Deliverables

- Final report PDF: [`report/SoftwareEngineering_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf`](report/SoftwareEngineering_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026.pdf)
- Poster reference: [`poster/index.html`](poster/index.html)
