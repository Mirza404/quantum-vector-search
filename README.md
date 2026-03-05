# Quantum Vector Search (Prototype)

A small but fully wired spike that follows the *Master Architecture Plan*:
- Treat every core concern (data loading, embeddings, search engines, benchmarking storage) as a strategy interface.
- Provide thin concrete implementations that we can replace without touching callers.
- Automate the benchmarking process so we can gather reproducible metrics before shipping any UI.

## What Ships Today
- `LocalCSVDataLoader(BaseDataLoader)` reads an immutable dataset from `backend/data/sample_dataset`.
- `MockCLIPEmbeddingGenerator(EmbeddingGenerator)` + `EmbeddingCache` implement the incremental embedding pipeline and caching discipline.
- `VectorMockEngine` and `QuantumMockEngine` already implement `SearchEngineStrategy`; `main.py` now exercises them with real dataset + embeddings.
- `CsvMarkdownStorage(BaseBenchmarkStorage)` appends benchmark runs to `artifacts/benchmarks/results.csv` and regenerates a human-readable `Report.md`.
- Two CLI utilities (`scripts/build_embeddings.py` and `scripts/run_benchmarks.py`) glue everything together.

## Strategy Interfaces at a Glance
| Concern | Interface | Concrete MVP | How to extend |
| --- | --- | --- | --- |
| Dataset retrieval | `BaseDataLoader` (`qvs.repository.base`) | `LocalCSVDataLoader` loads metadata + image paths from a CSV. | Implement `SQLDataLoader`, `S3DataLoader`, etc. and return `Dataset` objects; `main.py`, embedding pipeline, and benchmarks never change. |
| Embeddings | `EmbeddingGenerator` (`qvs.pipeline.embedding`) | `MockCLIPEmbeddingGenerator` (deterministic, CPU friendly). | Wrap CLIP, OpenCLIP, or any encoder; `build_embeddings.py` only depends on the interface. |
| Search engines | `SearchEngineStrategy` (`qvs.engines`) | `VectorMockEngine`, `QuantumMockEngine`. | Drop in FAISS, Qiskit, or hardware clients; benchmarking + API code already expect the shared interface. |
| Benchmark storage | `BaseBenchmarkStorage` (`qvs.benchmark.storage`) | `CsvMarkdownStorage` appends CSV rows and rewrites `Report.md`. | Swap with `DatabaseStorage` or cloud writers without touching `run_benchmarks.py`. |

## Repository Layout
```
.
├── README.md
└── backend
    ├── data/sample_dataset/
    │   ├── images/*.jpg      # lightweight placeholders to keep paths stable
    │   ├── metadata.csv      # id,text,image_path
    │   └── ground_truth.json # 4 predefined benchmark queries
    ├── main.py               # demo entrypoint that loads the dataset + strategies
    ├── scripts/
    │   ├── build_embeddings.py   # incremental embedding cache builder
    │   └── run_benchmarks.py     # automated benchmarking harness
    ├── src/qvs/
    │   ├── benchmark/            # models + CsvMarkdownStorage
    │   ├── engines/              # strategy interface + mock engines
    │   ├── pipeline/             # embedding generators + cache helpers
    │   └── repository/           # dataset abstractions + LocalCSV loader
    └── pyproject.toml
```

## Getting Started
1. **Install dependencies**
   ```bash
   cd backend
   uv pip install -e .
   ```
2. **Build (or refresh) embeddings** — the cache lives inside the dataset directory and automatically de-duplicates unchanged rows.
   ```bash
   PYTHONPATH=src python scripts/build_embeddings.py --dimension 16
   # rerun after editing metadata.csv; unchanged rows are reused
   ```
3. **Run the console demo** — now powered by the repository + embedding strategy stack.
   ```bash
   PYTHONPATH=src python main.py
   ```
   The script loads the dataset via `LocalCSVDataLoader`, hydrates embeddings from the cache (or regenerates them on the fly), embeds the first ground-truth query, and prints the ranked outputs from both engines.
4. **Collect benchmark data** — resumable and append-only by design.
   ```bash
   PYTHONPATH=src python scripts/run_benchmarks.py --dimensions 8 16 --top-k 3
   ```
   - The harness skips `(query_id, engine_name, dimension)` tuples that already exist in `artifacts/benchmarks/results.csv`.
   - Every appended row immediately regenerates `Report.md` with per-engine summaries and the 10 most recent runs.
   - State-preparation time is tracked separately for quantum engines so we can report the exact overhead called out in the benchmarking plan.

## Embedding Cache Details
- `scripts/build_embeddings.py` relies on the `EmbeddingGenerator` strategy. Today it uses `MockCLIPEmbeddingGenerator`, but swapping to CLIP just means providing another implementation.
- Cached files live under `data/<dataset>/cache/` (`embeddings.npy` + `manifest.json`). The manifest records a SHA-256 hash of each text row, so re-running the script after a typo fix only recomputes affected rows.
- Use `--force` to rebuild everything, or `--dimension` to generate multiple cache versions (the manifest enforces the dimension to prevent accidental reuse).

## Benchmarking Workflow
1. Ensure the embedding cache contains at least as many dimensions as the test run requires.
2. Maintain the ground-truth JSON (query id + text + target image id). The harness reads it via the repository + strategy stack so it also benefits from future loaders.
3. Results are kept in CSV form for easy diffing, while `Report.md` is machine-regenerated for humans. Both files live under `backend/artifacts/benchmarks/` (ignored by git so local experiments stay local).
4. When datasets or ground-truth fixtures change, follow the "Clean Slate" protocol from the benchmarking strategy: delete `cache/`, `results.csv`, and `Report.md`, then re-run the scripts.

## Extending the System
- To add a database-backed dataset, create `DatabaseDataLoader(BaseDataLoader)` and update configuration to instantiate it—no other code moves.
- To plug in a real quantum backend, subclass `SearchEngineStrategy`, report metadata in `SearchResult.meta`, and the benchmarking CLI will automatically capture timings + accuracy for it.
- To persist results elsewhere, drop a new `BaseBenchmarkStorage` implementation; `run_benchmarks.py` accepts the interface, so wiring in DynamoDB/Postgres later is trivial.

If you need a refresher on the broader context, keep `docs/ARCHITECTURE.md` and `docs/BENCHMARKING_STRATEGY.md` nearby—they capture the master plan that this code now enforces.
