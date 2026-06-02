# Backend

Benchmarking harness for classical and quantum-inspired search engines. For setup and running, see the root `README.md`.

## Package structure

```
src/
|-- benchmark/   # dataclasses, storage strategies, DatabaseStorage
|-- engines/     # SearchEngineStrategy base + engine implementations
|-- pipeline/    # EmbeddingGenerator interface, CLIPEmbeddingModel, mock
`-- repository/  # DataLoader interface, DirectoryDataLoader
```

## Dataset

The number of images to import is set in `config/dataset.yaml` (`num_images`). Run the import script once to download images as WebP and generate `data/ground_truth.jsonc`:

```bash
python3 scripts/import_dataset.py
```

Then encode the images into the database:

```bash
python3 scripts/index_dataset.py
```

## Configuration

`config/benchmarks.yaml` - comment out entries to skip without changing code. Each key is explained inline in that file.

`config/dataset.yaml` - set `num_images` to control how many Flickr30k images `import_dataset.py` pulls.

CLI flags override `benchmarks.yaml` for one-off runs: `--shots-values`, `--layers-values`, `--dimensions`, `--clip-model`, `--device`, `--batch-size`.

MRR is computed on the top-k result list returned by each engine. The default
is `top_k: 10`, configured in `config/benchmarks.yaml`, so benchmark MRR and
live-search MRR use the same cutoff.

Engine-count convention: the active benchmark/live-search set has 7 engines
(3 classical, 4 quantum or hybrid). Stored benchmark results can show an 8th
engine ID, `hybrid_hnsw_swap_test_ibm`, because the IBM hardware validation is
run separately at dimension 2 with two candidates and 32 shots. Treat IBM as a
validation data point, not as part of the normal simulator sweep.

## IBM Quantum smoke test

Set `IBM_QUANTUM_TOKEN` in `backend/.env` first. Keep `IBM_QUANTUM_ALLOW_PAID=false`.

```bash
python3 scripts/run_ibm_smoke.py
```

This runs one tiny 3-qubit hybrid HNSW + swap-test rerank on IBM hardware.

IBM hardware is intentionally isolated from frontend search and default benchmarks. It should be run only as an explicit validation because QPU queue time and free Open Plan quota are limited.

For a one-time report dataset, run:

```bash
python3 scripts/run_ibm_validation.py
```

This writes `hybrid_hnsw_swap_test_ibm` rows to the database for 20 queries at dimension 2, 2 candidates, and 32 shots. Existing rows are skipped.

Current saved IBM validation data used 80 seconds of Open Plan QPU time and produced average MRR 0.125. Treat it as a hardware validation data point, not as a like-for-like comparison with full simulator benchmarks.

## Database

Connection is configured via `backend/.env` (copy from `.env.example`). `DatabaseStorage` reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` automatically on import.
