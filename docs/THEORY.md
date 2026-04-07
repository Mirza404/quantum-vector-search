# Theory Reference

A cheat sheet for every theoretical concept in this project. For full explanations with build-up, see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## Similarity Metrics

All three metrics give **the same ranking** once vectors are L2-normalised (which this project always does in `CLIPEmbeddingModel.encode_texts()` and `encode_images()`).

| Metric | Formula | Engine that uses it | File |
|---|---|---|---|
| **Cosine similarity** | (a . b) / (||a|| . ||b||) | `BruteForceCosineEngine` | `backend/src/engines/brute_force_cosine.py` |
| **L2 distance** | ||a - b|| | `FaissFlatEngine`, pgvector HNSW | `backend/src/engines/faiss_flat.py` |
| **Squared inner product** | \|<psi\|phi>\|^2 | `QiskitSwapTestEngine` (swap test) | `backend/src/engines/qiskit_swaptest.py` |

> **Analogy:** Think of three different rulers (inches, centimetres, and a weird ruler that squares the reading). They give different numbers, but they all agree on which two objects are closer together. That's what "equivalent for ranking" means.

**Why they're equivalent on unit vectors:** After normalisation, cosine = dot product, and L2^2 = 2 - 2*cos(theta). All monotonic transforms of each other, so sorting order is identical.

**In one sentence:** The project uses three different formulas that all measure the same thing (how similar two vectors are) because the vectors are always normalised first.

<details>
<summary>Self-test</summary>

**Q: If two normalised vectors have cosine similarity 0.9, what's their squared inner product?**
A: 0.81 (just 0.9 squared). The swap test would report this value.

**Q: Why can we compare MRR across engines even though they use different metrics?**
A: Because on normalised vectors all metrics produce the same ranking, so MRR (which depends only on ranking) is directly comparable.
</details>

---

## CLIP Details

**CLIP** (Contrastive Language-Image Pre-training) is the AI model that converts both text and images into vectors in a shared space. Implemented in `backend/src/pipeline/clip_model.py`.

| Property | Value |
|---|---|
| Architecture | Vision Transformer (images) + Transformer (text) |
| Variant used | ViT-B/32 -- "Base" size, 32x32 pixel patches |
| Input resolution | 224x224 pixels |
| Parameters | ~151M total (~87M image encoder + ~63M text encoder) |
| Output dimension | 512 floats |
| Training data | ~400M image-caption pairs, contrastive loss |

> **Analogy:** CLIP is like a translator who learned to speak both "image" and "text" by studying 400 million captioned photos. When you give it a photo or a sentence, it responds with the same kind of 512-number summary -- and similar things get similar summaries.

- Runs locally via PyTorch -- no API key needed
- Auto-detects GPU: CUDA -> Apple MPS -> CPU fallback (see `CLIPEmbeddingModel._resolve_device()`)
- The project truncates the 512-dim output to smaller sizes (e.g. 64, 128) to study how dimension affects accuracy and quantum cost. Truncation happens in `_prepare_vectors()` in `backend/scripts/run_benchmarks.py`

**In one sentence:** CLIP turns both text and images into comparable 512-number lists, so "a dog on a beach" and a photo of a dog on a beach end up with similar numbers.

<details>
<summary>Self-test</summary>

**Q: Why can we search for images using text, even though they're completely different data types?**
A: Because CLIP maps both into the same 512-dimensional vector space. Similar meanings -> nearby vectors, regardless of input type.

**Q: What happens when we truncate from 512 to 64 dimensions?**
A: We keep the first 64 components (which carry the most information) and discard the rest. Accuracy drops slightly, but qubit requirements also drop (from 9 qubits per register to 6).
</details>

---

## Swap Test Formula

The **swap test** is the quantum circuit at the heart of this project (`backend/src/engines/qiskit_swaptest.py`, method `_run_swap_test()`).

```
P(ancilla = 0) = (1 + |<psi|phi>|^2) / 2

similarity = sqrt(max(0, 2 * P(0) - 1))
```

- **P(0)** = probability of measuring the ancilla qubit as 0 (estimated by running the circuit many times)
- **|<psi|phi>|^2** = squared cosine similarity of the two vectors
- **Shot noise standard error:** 1/sqrt(N_shots). With 2048 shots, error ~ 0.022 in P(0)

> **Analogy:** Imagine flipping a biased coin 2048 times to estimate how biased it is. Each flip gives you one bit of information. The more flips (shots), the better your estimate of the true bias (similarity).

**In one sentence:** The swap test estimates how similar two vectors are by running a quantum circuit many times and counting how often the result is 0.

<details>
<summary>Self-test</summary>

**Q: If two vectors are identical (similarity = 1.0), what is P(0)?**
A: P(0) = (1 + 1) / 2 = 1.0. The ancilla always measures 0.

**Q: If two vectors are orthogonal (similarity = 0), what is P(0)?**
A: P(0) = (1 + 0) / 2 = 0.5. The ancilla is a fair coin -- maximum uncertainty.
</details>

---

## Qubit Counts

Each swap test needs **two vector registers** (one for query, one for database vector) plus **one ancilla qubit**. Each register needs log2(dim) qubits because of amplitude encoding.

| Vector dim | Qubits per register | Total (swap test) |
|---|---|---|
| 64 | 6 | 6 + 6 + 1 = **13** |
| 128 | 7 | 7 + 7 + 1 = **15** |
| 512 | 9 | 9 + 9 + 1 = **19** |

These numbers come from the actual Qiskit circuit in `_run_swap_test()` and are stored in the `num_qubits` column of `benchmark_results`.

> **Analogy:** Amplitude encoding is like super-efficient compression -- you can store 64 numbers using only 6 qubits (because 2^6 = 64). The catch: decompressing (state preparation) is expensive.

**In one sentence:** A 64-dimensional swap test needs 13 qubits total, well within current hardware limits (~1000 qubits), but circuit depth is the real constraint.

<details>
<summary>Self-test</summary>

**Q: Why does doubling the vector dimension only add 2 qubits (one per register)?**
A: Because qubit count grows as log2(dim). Going from 64 to 128 is log2(128) - log2(64) = 7 - 6 = 1 extra qubit per register.

**Q: Are 13-15 qubits feasible on current hardware?**
A: Yes, current IBM chips have 1000+ qubits. The bottleneck is circuit depth (how many sequential gates), not qubit count.
</details>

---

## Evaluation: MRR

**Mean Reciprocal Rank** -- the main quality metric, computed in `_mrr()` in `backend/scripts/run_benchmarks.py`.

```
MRR = average of (1 / rank of first correct result) across all queries
```

- Correct image at rank 1 -> score 1.0
- Correct image at rank 2 -> score 0.5
- Correct image at rank 5 -> score 0.2

> **Analogy:** MRR measures "how far does a user scroll before finding what they want?" MRR = 1.0 means the right answer is always on top. MRR = 0.5 means the user typically has to look at the second result.

Key details:
- The harness ranks **all** dataset images (no top-K cutoff) to capture the true rank
- Each query maps to exactly one correct image: strip `query_` prefix from query ID to get the target image ID (see `BenchmarkQuery.target_id` in `backend/src/benchmark/models.py`)
- The benchmark report (`backend/docs/benchmark_report.md`) is generated by `backend/scripts/generate_report.py`

**In one sentence:** MRR tells you how close to the top the correct answer appears, averaged across all queries.

<details>
<summary>Self-test</summary>

**Q: If an engine gets MRR 0.8, what does that roughly mean?**
A: On average, the correct image is around rank 1.25 -- almost always first, occasionally second.

**Q: Why does the harness rank ALL images instead of just returning top-10?**
A: To measure the true rank of the correct result. If it's at rank 15, a top-10 cutoff would miss it entirely and give MRR = 0, hiding useful information.
</details>

---

## pgvector Storage

**pgvector** is a PostgreSQL extension that adds vector operations. Used in `db/migrations/up/1_initial_schema.sql`.

- `vector(512)` column type for storing CLIP embeddings
- Distance operators: `<->` (L2), `<#>` (negative dot product), `<=>` (cosine)
- Index types: IVFFlat and HNSW for approximate nearest-neighbour queries

The `image_vectors` table uses HNSW with cosine distance:
```sql
CREATE INDEX image_vectors_embedding_idx
    ON image_vectors USING hnsw (embedding vector_cosine_ops);
```

Example query (what the live API will use):
```sql
SELECT id FROM image_vectors
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

**Why pgvector instead of Pinecone/Weaviate/etc.?** The project already runs PostgreSQL for benchmark results (same Docker Compose in `db/docker-compose.yml`, same `.env`, same backup workflow). For our dataset size (~20 images), a separate vector database would be overkill.

**In one sentence:** pgvector lets us store and search vectors inside the same PostgreSQL database we already use for benchmark results.

<details>
<summary>Self-test</summary>

**Q: What does the `<=>` operator do in pgvector?**
A: It computes cosine distance between two vectors -- used for nearest-neighbour queries.

**Q: Why is HNSW indexing not critical for this project's dataset?**
A: With only ~20 images, brute-force search is instant. HNSW matters at thousands to millions of vectors.
</details>

---

## Design Decisions

### Strategy Pattern

All engines implement `SearchEngineStrategy` (defined in `backend/src/engines/base.py`): `build_index()` + `search()`. The benchmark harness in `run_benchmarks.py` iterates over engines without knowing which one is running.

The same pattern applies to:
- `EmbeddingGenerator` (`backend/src/pipeline/base.py`) -- swappable embedding models
- `BaseDataLoader` (`backend/src/repository/base.py`) -- swappable data sources

> **Analogy:** Like USB ports -- any device that follows the USB spec can plug in. Any engine that implements `build_index()` + `search()` can be benchmarked.

### Configuration-Driven Benchmarking

`backend/config/benchmarks.yaml` defines engines, dimensions, shots, and layers. Comment out any line to skip it. CLI flags (`--dimensions`, `--shots-values`, `--layers-values`) override YAML for one-off runs.

### Benchmark Result Storage

Each `(query_id, engine_name, dimension, shots, layers)` is a unique **run key** (see `uq_run_key` constraint in `db/migrations/up/4_drop_top_k_column.sql`). Classical engines use `shots = -1, layers = -1` as sentinel values. Re-running the same configuration overwrites the row (upsert). New parameter values append new rows.

### Live Search vs. Benchmarking

| | Benchmarking | Live API (planned) |
|---|---|---|
| **Ranks** | All images (full ranking) | Top-K only |
| **Purpose** | Accurate MRR measurement | User-facing search |
| **Engine** | Any (configurable) | pgvector HNSW |

**In one sentence:** The strategy pattern makes engines swappable, YAML makes experiments configurable, and PostgreSQL stores everything with upsert-on-conflict semantics.
