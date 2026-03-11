# Action Items

## 1. Set Up Database via Docker and Remove CSV Storage

The architecture plan in `docs/NOTES.md` (Phase 4) mandates writing benchmark results directly to a database — no CSV files. Currently, `CsvMarkdownStorage` is used and no Docker setup exists.

**What needs to happen:**

- Create a `db/` directory at the project root (outside `backend/`) containing:
  - `docker-compose.yml` — spins up a bare PostgreSQL instance with no project-specific knowledge
  - `schema.sql` — creates the benchmark results table structure
  - `data.sql` — for exporting/importing actual benchmark data between team members
- In `backend/src/qvs/benchmark/`, replace `CsvMarkdownStorage` with a `DatabaseStorage` implementation that writes rows directly to the database via a DSN connection string (read from an environment variable).
- Delete the generated output files: `backend/artifacts/benchmarks/results.csv` and `backend/artifacts/benchmarks/Report.md`. The `artifacts/` folder can be removed entirely.
- Update `backend/scripts/run_benchmarks.py` to use `DatabaseStorage` instead of `CsvMarkdownStorage`.
- Update `backend/src/qvs/benchmark/__init__.py` to export the new class.

---

## 2. Remove the Embedding Cache System

The file-hashing/caching system (`EmbeddingCache`, `_hash_text`, `manifest.json`) was built to skip recomputing unchanged embeddings. This is being replaced by a simple config file approach (see item 3).

**What needs to happen:**

- Delete `backend/src/qvs/pipeline/cache.py` entirely.
- Delete `backend/scripts/build_embeddings.py` entirely.
- Delete the generated cache files: `backend/data/sample_dataset/cache/embeddings.npy` and `backend/data/sample_dataset/cache/manifest.json` (and the `cache/` directory).
- Update `backend/src/qvs/pipeline/__init__.py` to remove exports for `EmbeddingCache`, `EmbeddingCacheEntry`, and `EmbeddingCacheSnapshot`.
- Update `backend/scripts/run_benchmarks.py` to remove the `_ensure_cache()` function and generate embeddings on the fly instead.
- Update `backend/main.py` to remove any cache-related imports or usage.

---

## 3. Replace Cache Skip Logic with a Config File

Currently `run_benchmarks.py` skips already-run benchmarks by checking the CSV. With the cache removed, a simple config file will control which engines, dimensions, and queries are active for a given run.

**What needs to happen:**

- Create `backend/config/benchmarks.yaml` with fields for active engines, dimensions, and query IDs. Comment out entries to skip them — no code changes needed between runs.
- Update `run_benchmarks.py` to read this config at startup and filter accordingly, instead of checking `storage.has_record()`.

---

## 4. Refactor Strategy Pattern — One File Per Class

The rule: each abstract strategy in its own file, each implementation in its own separate file. No implementations inside `base.py` or `__init__.py`.

**Current problems (3 violations found):**

**`engines/`** — `SearchEngineStrategy` and `SearchResult` live in `__init__.py`, not a dedicated base file. Implementations (`vector_mock.py`, `quantum_mock.py`, `faiss_flat.py`, `qiskit_swaptest.py`) are already correctly separated.
- Create `engines/base.py` and move the abstract class + `SearchResult` there.
- Update `engines/__init__.py` to re-export from `base.py` and the implementation files.

**`pipeline/`** — `EmbeddingGenerator` (abstract) and `MockCLIPEmbeddingGenerator` (implementation) both live in `embedding.py`.
- Create `pipeline/base.py` with only `EmbeddingGenerator`.
- Create `pipeline/mock_clip.py` with only `MockCLIPEmbeddingGenerator`.
- Delete `embedding.py`.
- Update `pipeline/__init__.py` accordingly.

**`benchmark/`** — `BaseBenchmarkStorage` (abstract) and `CsvMarkdownStorage` (implementation) both live in `storage.py`. This is resolved naturally by item 1: split into `benchmark/base.py` (abstract only) and `benchmark/db_storage.py` (the new `DatabaseStorage`). Delete `storage.py`.

**`repository/`** — Already correct. `base.py` has the abstract, `local_csv.py` has the implementation. No changes needed.

---

## 5. Change `target_id` to `target_ids` (List)

A single query should be able to map to multiple correct results (e.g., a "nature" query matching several images). Currently `target_id` is a single string everywhere.

**What needs to happen:**

- `backend/data/sample_dataset/ground_truth.json` — rename the key from `"target_id"` to `"target_ids"` and wrap each value in a list.
- `backend/src/qvs/benchmark/models.py` — change `target_id: str` to `target_ids: List[str]` in both `BenchmarkQuery` and `BenchmarkResult`.
- `backend/scripts/run_benchmarks.py` — update `_accuracy_score()` to accept a list of target IDs and find the best-ranking match among all of them.

---

## 6. Delete `STRUCTURE.md`

Delete `STRUCTURE.md` from the project root. It is unnecessary overhead — the directory layout speaks for itself.

---

## 7. Rewrite Root `README.md`

The current `README.md` is too detailed and technical for a project overview. Rewrite it to be:

- A brief description of what the project is.
- A pointer to the two main areas: `backend/` (Python benchmarking pipeline) and the future React frontend.
- Minimal getting-started steps (spin up DB, install deps, run benchmarks).
- A pointer to `backend/README.md` for backend-specific details.

No strategy interface tables, no deep technical explanations.

---

## 8. Create `backend/README.md`

Create a README specific to the backend containing:

- How to spin up the database with Docker.
- How to install Python dependencies.
- How to run benchmarks (see item 9 for the correct command).
- How to use `backend/config/benchmarks.yaml` to control which runs execute.
- The environment variable used for the DB connection string.
- A brief overview of the `src/qvs/` package structure.

---

## 9. Execution Convention

All benchmark scripts must be run from inside `backend/src/` using `python3`:

```bash
cd backend/src && python3 ../../scripts/run_benchmarks.py
```

Update all documentation, script headers, and inline comments to reflect this. Never use `python`, always `python3`.

---

## 10. Update `docs/NOTES.md`

The file is the source of truth for the paper and needs to reflect the actual current state of the project after all the above changes are applied.

**What to update:**

- Add a **"Current Status"** section near the top that briefly lists which phases are complete, in progress, or pending. This gives an accurate snapshot for writing the paper.
- In **Phase 2 (Embedding Pipeline)**, remove any mention of `build_embeddings.py` and the incremental hash cache — those no longer exist. Describe embeddings as being generated on the fly per benchmark run.
- In **Phase 4 (Benchmarking Storage)**, confirm the three-layer DB structure described there (`docker-compose.yml`, `schema.sql`, `data.sql` in `db/`) matches what was actually created in item 1 above. Correct any discrepancies.
- Remove or update any references to CSV files — there is no CSV in the current design.
- Ensure the config-file-driven benchmarking approach (item 3) is reflected in Section 6 (Configuration-Driven Benchmarking Strategy).

The goal is that someone reading `NOTES.md` can understand the full project design as it actually exists, not as it was originally planned.
