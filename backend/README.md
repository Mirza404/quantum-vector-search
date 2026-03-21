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

The number of images to import is set in `config/dataset.yaml` (`num_images`). Run the import script once to download images as WebP and generate `data/ground_truth.jsonc`:

```bash
python3 scripts/import_dataset.py
```

Then encode the images into the database:

```bash
python3 scripts/index_dataset.py
```

## Configuration

`config/benchmarks.yaml` — comment out entries to skip without changing code. Each key is explained inline in that file.

`config/dataset.yaml` — set `num_images` to control how many Flickr30k images `import_dataset.py` pulls.

CLI flags override `benchmarks.yaml` for one-off runs: `--shots-values`, `--layers-values`, `--dimensions`, `--clip-model`, `--device`, `--batch-size`.

MRR is computed over the full ranking — no top_k cutoff. The harness retrieves all dataset images and measures the true rank of the correct result.

## Database

Connection is configured via `backend/.env` (copy from `.env.example`). `DatabaseStorage` reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` automatically on import.
