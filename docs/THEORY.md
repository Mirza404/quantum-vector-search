# Theory Reference

Quick-reference cheat sheet for every theoretical concept in this project. For full build-up explanations, see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## Similarity Metrics

This project always **L2-normalises** vectors first (in `CLIPEmbeddingModel.encode_texts()` and `encode_images()` in `backend/src/pipeline/clip_model.py`). Once normalised, all three metrics below produce **the same ranking**.

| Metric | Formula | Engine | File |
|---|---|---|---|
| **Cosine similarity** | (a . b) / (\|\|a\|\| * \|\|b\|\|) | `BruteForceCosineEngine` | `brute_force_cosine.py` |
| **L2 distance** | \|\|a - b\|\| | `FaissFlatEngine` | `faiss_flat.py` |
| **Squared inner product** | \|<psi\|phi>\|^2 | `QiskitSwapTestEngine` | `qiskit_swaptest.py` |

> **Analogy:** Three different rulers -- inches, centimetres, and one that squares the reading. Different numbers, but they all agree on which two objects are closer.

**Why equivalent on unit vectors:** After normalisation, cosine = dot product, and L2^2 = 2 - 2*cos(theta). All are monotonic transforms, so sort order is identical.

<details><summary>Self-test</summary>

**Q: If two normalised vectors have cosine similarity 0.9, what's their squared inner product?**
A: 0.81 (0.9 squared). The swap test reports this value.

**Q: Why can we compare MRR across engines that use different metrics?**
A: On normalised vectors, all metrics produce the same ranking, so MRR (which depends only on ranking) is directly comparable.
</details>

---

## CLIP

**CLIP** (Contrastive Language-Image Pre-training) converts both text and images into vectors in a shared space. Implemented in `backend/src/pipeline/clip_model.py`.

| Property | Value |
|---|---|
| Variant used | **ViT-B/32** (Vision Transformer, 32x32 patches) |
| Output | **512 floats** per input |
| Training data | ~400M image-caption pairs |
| Device | Auto-detects CUDA / MPS / CPU (`_resolve_device()`) |

> **Analogy:** A translator who learned both "image" and "text" by studying 400 million captioned photos. Give it a photo or a sentence -- it responds with the same kind of 512-number summary, and similar things get similar summaries.

- The project **truncates** the 512-dim output to smaller sizes (64, 128, etc.) to study how dimension affects accuracy and quantum cost -- see `_prepare_vectors()` in `backend/scripts/run_benchmarks.py`
- For testing without loading the real model: `MockCLIPEmbeddingGenerator` in `backend/src/pipeline/mock_clip.py`

<details><summary>Self-test</summary>

**Q: Why can we search for images using text?**
A: CLIP maps both into the same 512-dim vector space. Similar meanings produce nearby vectors regardless of input type.

**Q: What happens when we truncate from 512 to 64 dimensions?**
A: We keep the first 64 components and discard the rest. Accuracy drops slightly, but qubit requirements also drop (9 qubits per register down to 6).
</details>

---

## Swap Test

The **swap test** is the quantum circuit at the heart of this project -- it estimates how similar two vectors are. Implemented in `QiskitSwapTestEngine._run_swap_test()` in `backend/src/engines/qiskit_swaptest.py`.

**The formula:**
```
P(ancilla = 0) = (1 + |<psi|phi>|^2) / 2
similarity = sqrt(max(0, 2 * P(0) - 1))
```

- **P(0)** = probability of measuring the ancilla qubit as 0 (estimated by running the circuit many times)
- **Shot noise standard error:** 1/sqrt(N_shots). With 2048 shots, error is ~0.022 in P(0)

> **Analogy:** Flipping a biased coin 2048 times to figure out how biased it is. Each flip gives one bit of info. More flips (shots) = better estimate of the true bias (similarity).

<details><summary>Self-test</summary>

**Q: If two vectors are identical (similarity = 1.0), what is P(0)?**
A: (1 + 1) / 2 = 1.0. The ancilla always measures 0.

**Q: If two vectors are orthogonal (similarity = 0)?**
A: (1 + 0) / 2 = 0.5. The ancilla is a fair coin -- maximum uncertainty.
</details>

---

## Qubit Counts

Each swap test needs **two registers** (query + database vector) plus **one ancilla qubit**. Each register uses log2(dim) qubits thanks to **amplitude encoding**.

| Vector dim | Qubits per register | Total |
|---|---|---|
| 64 | 6 | **13** |
| 128 | 7 | **15** |
| 512 | 9 | **19** |

These come from the actual Qiskit circuit in `_run_swap_test()` and are stored in `benchmark_results.num_qubits`.

> **Analogy:** Amplitude encoding is like extreme compression -- 64 numbers stored in just 6 qubits (2^6 = 64). The catch: decompressing (state preparation) is expensive.

<details><summary>Self-test</summary>

**Q: Why does doubling the dimension only add 2 qubits?**
A: Qubit count grows as log2(dim). 128 vs 64: log2(128) - log2(64) = 7 - 6 = 1 extra per register.

**Q: Are 13-15 qubits feasible today?**
A: Yes -- IBM chips have 1000+ qubits. The real bottleneck is circuit depth, not qubit count.
</details>

---

## MRR (Mean Reciprocal Rank)

The main quality metric. Computed in `_mrr()` in `backend/scripts/run_benchmarks.py`.

```
MRR = average of (1 / rank of first correct result) across all queries
```

- Rank 1 = score 1.0, rank 2 = 0.5, rank 5 = 0.2

> **Analogy:** "How far does a user scroll before finding the right answer?" MRR 1.0 = always on top. MRR 0.5 = typically second result.

- The harness ranks **all** dataset images (no top-K cutoff) to capture the true rank
- Each query maps to one correct image: strip `query_` prefix from query ID (see `BenchmarkQuery.target_id` in `backend/src/benchmark/models.py`)
- Report generated by `backend/scripts/generate_report.py`

<details><summary>Self-test</summary>

**Q: Why rank ALL images instead of returning top-10?**
A: To measure the true rank. If the correct result is at rank 15, a top-10 cutoff would give MRR = 0, hiding useful info.
</details>

---

## pgvector Storage

**pgvector** is a PostgreSQL extension for vector operations. Set up in `db/migrations/up/1_initial_schema.sql`.

- `vector(512)` column stores CLIP embeddings in `image_vectors` table
- Distance operators: `<->` (L2), `<=>` (cosine)
- HNSW index for approximate nearest-neighbour (not used in benchmarking -- only for future live search)

**Why pgvector instead of Pinecone/Weaviate?** The project already runs PostgreSQL for benchmark results (same Docker Compose, same `.env`). For ~20 images, a separate vector DB would be overkill.

<details><summary>Self-test</summary>

**Q: Why isn't HNSW used for benchmarking?**
A: HNSW is approximate. Benchmarking needs exact results to fairly measure MRR.
</details>

---

## Design Decisions

- **Strategy Pattern:** All engines implement `SearchEngineStrategy` (`build_index()` + `search()`) in `backend/src/engines/base.py`. Same pattern for `EmbeddingGenerator` and `BaseDataLoader`. Adding a new engine = implementing the interface, nothing else changes.

> **Analogy:** Like USB ports -- any device that follows the spec works.

- **Config-driven benchmarking:** `backend/config/benchmarks.yaml` defines engines, dimensions, shots, layers. Comment out a line to skip it. CLI flags override YAML for one-off runs.
- **Upsert storage:** Each `(query_id, engine_name, dimension, shots, layers)` is a unique run key (see `uq_run_key` in `db/migrations/up/4_drop_top_k_column.sql`). Re-running overwrites; new params append.
