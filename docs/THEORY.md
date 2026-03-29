# Theory Reference

Quick reference for the theoretical concepts behind this project. For the full explanations,
see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## Similarity Metrics

All three metrics produce the same ranking on L2-normalised vectors:

| Metric | Formula | Used by |
|---|---|---|
| Cosine similarity | (a · b) / (‖a‖ · ‖b‖) | `BruteForceCosineEngine` |
| L2 distance | ‖a − b‖ | `FaissFlatEngine`, pgvector HNSW |
| Squared dot product | \|⟨ψ\|φ⟩\|² | `QiskitSwapTestEngine` (via swap test) |

After L2 normalisation: cosine = dot product, and L2² = 2 − 2·cos θ. All equivalent for
ranking.

---

## CLIP Details

| Property | Value |
|---|---|
| Architecture | Vision Transformer (image) + Transformer (text) |
| Variant | ViT-B/32 — "Base" size, 32×32 pixel patches |
| Input resolution | 224×224 |
| Parameters | ~151M total (~87M image + ~63M text) |
| Output dimension | 512 |
| Training data | ~400M image-caption pairs, contrastive loss |

Runs locally via PyTorch. Auto-detects CUDA GPU → Apple MPS → CPU fallback. No API key
required.

---

## Swap Test Formula

```
P(ancilla = 0) = (1 + |⟨ψ|φ⟩|²) / 2

similarity = √(max(0, 2 × P(0) − 1))
```

Shot noise standard error: 1/√N_shots. With 2048 shots, error ≈ 0.022 in P(0).

See [LEARNING_ROADMAP.md — Part 6](LEARNING_ROADMAP.md#part-6--amplitude-encoding-and-the-swap-test) for the full explanation.

---

## Qubit Counts

| Vector dim | Qubits per register | Total (swap test) |
|---|---|---|
| 64 | 6 | 13 (6+6+1 ancilla) |
| 128 | 7 | 15 (7+7+1 ancilla) |

---

## Evaluation: MRR

```
MRR = average of (1 / rank of first correct result) across all queries
```

The harness retrieves the full ranking — all dataset images ranked from most to least similar.
No top-K cutoff in benchmarking. `top_k` exists only in the API as a pagination parameter.

Each query maps to exactly one correct image, derived by stripping the `query_` prefix from
the query ID.

---

## pgvector Storage

pgvector is a PostgreSQL extension that adds:

- `vector(n)` column type for fixed-dimension float arrays.
- Distance operators: `<->` (L2), `<#>` (negative dot product), `<=>` (cosine).
- Index support: IVFFlat and HNSW for approximate nearest-neighbour queries.

The `image_vectors` table uses HNSW with cosine distance:

```sql
SELECT id FROM image_vectors
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

**Why pgvector instead of Pinecone, Weaviate, etc.?** The project already runs PostgreSQL for
benchmark results. Same Docker Compose, same DSN, same backup workflow. For our dataset size
(hundreds of images), pgvector is more than sufficient.

---

## Design Decisions

### Strategy Pattern

All engines implement `SearchEngineStrategy` (`build_index()` + `search()`). The benchmark
harness iterates over a list of strategy instances without knowing which engine is running.
Adding a new engine means implementing the interface — nothing else changes. The same pattern
is applied to `EmbeddingGenerator` and `BaseDataLoader`.

### Configuration-Driven Benchmarking

`benchmarks.yaml` defines engines, dimensions, shots, and layers. CLI flags can override any
value. Adding a dimension or engine requires only a YAML edit.

### Benchmark Result Storage

Each `(query_id, engine_name, dimension, shots, layers)` tuple is a unique **run key**.
Classical engines use shots = −1, layers = −1 as sentinels. Re-running the same configuration
overwrites the row (upsert). New parameter values append new rows.

### Live Search vs. Benchmarking

The benchmark harness retrieves and ranks all images — full ranking for accurate MRR. The
live API returns only top-K with similarity scores, so the frontend can signal when even the
best match scores poorly.
