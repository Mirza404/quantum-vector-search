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

## Configuration

`config/benchmarks.yaml` controls each benchmark run. Comment out entries to skip without changing code.

```yaml
engines:       # vector_mock_cosine | faiss_flat_l2 | quantum_mock_sampler | qiskit_swap_test
dimensions:    # truncated from CLIP's 512-dim output
queries:       # IDs from data/sample_dataset/ground_truth.json
top_k: 3
shots: 2048
layers: 2
```

CLI flags override the YAML: `--top-k`, `--shots`, `--layers`, `--dimensions`, `--clip-model`, `--device`, `--batch-size`.

## Database

`DatabaseStorage` reads `QVS_BENCHMARK_DSN` from the environment (bootstrapped from `.env`). To override:

```bash
QVS_BENCHMARK_DSN=postgresql://user:pass@host:5432/db python3 scripts/run_benchmarks.py
```
