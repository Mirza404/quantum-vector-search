# Backend

Benchmarking harness for classical and quantum-inspired search engines. For setup and running, see the root `README.md`.

## Package structure

```
src/qvs/
├── benchmark/   # dataclasses, storage strategies, DatabaseStorage
├── engines/     # SearchEngineStrategy base + all four engine implementations
├── pipeline/    # EmbeddingGenerator interface, CLIPEmbeddingModel, mock
└── repository/  # DataLoader interface, LocalCSVDataLoader
```

## Dataset

Run the import script once to download 20 Flickr30k images as WebP and generate `data/ground_truth.jsonc`:

```bash
python3 scripts/import_dataset.py
```

The script prints the query IDs — copy them into `config/benchmarks.yaml` under `queries:`.
Then encode the images into the database:

```bash
python3 scripts/index_dataset.py
```

## Configuration

`config/benchmarks.yaml` controls each benchmark run. Comment out entries to skip without changing code.

```yaml
engines:          # brute_force_cosine | faiss_flat_l2 | quantum_mock_sampler | qiskit_swap_test
dimensions:       # truncated from CLIP's 512-dim output
queries:          # IDs from data/ground_truth.jsonc
shots_values:     # list — quantum engines only
layers_values:    # list — quantum engines only
```

MRR is computed over the full ranking — no top_k cutoff. The harness always retrieves all dataset images and ranks them; MRR is the reciprocal of the correct image's true position.

CLI flags override the YAML: `--shots-values`, `--layers-values`, `--dimensions`, `--clip-model`, `--device`, `--batch-size`.

## Database

Connection is configured via `backend/.env` (copy from `.env.example`). `DatabaseStorage` reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` automatically on import.
