# Theory Reference

Quick-reference cheat sheet for every theoretical concept in this project. For full explanations: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md). For the qRAM and scaling analysis: [QUANTUM_SEARCH_ANALYSIS.md](QUANTUM_SEARCH_ANALYSIS.md).

---

## Similarity Metrics

This project **L2-normalises** all vectors first (in `CLIPEmbeddingModel.encode_texts()` and `encode_images()`). Once normalised, all three metrics produce **the same ranking**.

| Metric | Formula | Engine | File |
|---|---|---|---|
| **Cosine similarity** | (a . b) / (\|\|a\|\| * \|\|b\|\|) | `BruteForceCosineEngine` | `brute_force_cosine.py` |
| **L2 distance** | \|\|a - b\|\| | `FaissFlatEngine` | `faiss_flat.py` |
| **Squared inner product** | \|<psi\|phi>\|^2 | `QiskitSwapTestEngine` | `qiskit_swaptest.py` |

> Three different rulers -- inches, centimetres, and one that squares the reading. Different numbers, same ranking of which objects are closer.

**Why equivalent on unit vectors:** cosine = dot product after normalisation. L2^2 = 2 - 2*cos(theta). All monotonic transforms, so sort order is identical.

<details><summary>Self-test</summary>

**Q: If two normalised vectors have cosine similarity 0.9, what's their squared inner product?**
A: 0.81 (0.9 squared). The swap test reports this value.

**Q: Why can we compare MRR across engines that use different metrics?**
A: On normalised vectors, all metrics produce the same ranking, so MRR is directly comparable.
</details>

---

## CLIP

**CLIP** (Contrastive Language-Image Pre-training) converts text and images into vectors in a shared 512-dim space. Implemented in `backend/src/pipeline/clip_model.py`.

| Property | Value |
|---|---|
| Variant | **ViT-B/32** (Vision Transformer, 32x32 patches) |
| Output | **512 floats** per input |
| Training data | ~400M image-caption pairs |
| Device | Auto-detects CUDA / MPS / CPU |

The project **truncates** to smaller sizes (64, 128) via `_prepare_vectors()` in `run_benchmarks.py`. For testing without GPU: `MockCLIPEmbeddingGenerator` in `mock_clip.py`.

<details><summary>Self-test</summary>

**Q: Why can we search for images using text?**
A: CLIP maps both into the same vector space. Similar meanings = nearby vectors.

**Q: What happens when we truncate from 512 to 64 dims?**
A: We keep the first 64 components. Accuracy drops slightly, but qubit count drops from 9 to 6 per register.
</details>

---

## Swap Test

Estimates |<psi|phi>|^2 -- squared cosine similarity. Implemented in `QiskitSwapTestEngine._run_swap_test()` in `qiskit_swaptest.py`.

**Formula:**
```
P(ancilla = 0) = (1 + |<psi|phi>|^2) / 2
similarity = sqrt(max(0, 2*P(0) - 1))
```

- **Shot noise error:** 1/sqrt(N_shots). With 2048 shots, error ~0.022 in P(0)

> Flipping a biased coin 2048 times to figure out how biased it is. More flips (shots) = better estimate.

<details><summary>Self-test</summary>

**Q: Identical vectors (similarity = 1.0) -- what is P(0)?**
A: 1.0. Ancilla always measures 0.

**Q: Orthogonal vectors -- what is P(0)?**
A: 0.5. Fair coin flip.
</details>

---

## Grover's Algorithm

Finds a marked item in N items using O(sqrt(N)) oracle queries instead of O(N) classical comparisons. Implemented in `QiskitGroverEngine` in `qiskit_grover.py`.

**How it works:**
1. Uniform superposition via Hadamard gates
2. Repeat floor(pi*sqrt(N)/4) times: oracle (phase flip on target) + diffusion (reflect around mean)
3. Measure -- target has probability ~1

**Key limitation:** Needs all N items in superposition simultaneously, which requires **qRAM** (doesn't exist). Without qRAM, state preparation costs O(N), cancelling the O(sqrt(N)) search savings.

**What the engine does:** Pre-computes the closest match classically, then runs Grover's circuit to find it. This isolates the search step so oracle call counts can be measured independently.

| N | Classical comparisons | Grover oracle calls |
|---|---|---|
| 100 | 100 | 8 |
| 1,000 | 1,000 | 25 |
| 1,000,000 | 1,000,000 | 785 |

<details><summary>Self-test</summary>

**Q: For N = 1,000,000, how many oracle calls?**
A: floor(pi * 1000 / 4) ~ 785.

**Q: Why does the engine pre-compute the answer classically?**
A: To build the oracle. Without qRAM, this O(N) step can't be avoided. The value is in measuring O(sqrt(N)) search scaling.
</details>

---

## Qubit Counts

Swap test needs **two registers** (query + data vector) plus **one ancilla**. Each register uses log2(dim) qubits via **amplitude encoding**.

| Vector dim | Qubits per register | Total |
|---|---|---|
| 64 | 6 | **13** |
| 128 | 7 | **15** |
| 512 | 9 | **19** |

Grover uses log2(N) **index qubits** where N = dataset size (padded to next power of 2).

> Amplitude encoding is extreme compression -- 64 numbers in 6 qubits (2^6 = 64). The catch: preparing the state takes O(64) gates.

<details><summary>Self-test</summary>

**Q: Why does doubling dimension only add ~1 qubit per register?**
A: Qubit count grows as log2(dim). log2(128) - log2(64) = 7 - 6 = 1.

**Q: Are 13-15 qubits feasible today?**
A: Yes for qubit count. The real bottleneck is circuit depth, not qubits.
</details>

---

## Operation Count -- Cross-Engine Scaling KPI

The only valid cross-engine "speed" comparison. Stored in `benchmark_results.oracle_calls`.

| Engine | Operations per query | Complexity |
|---|---|---|
| Classical (brute force, FAISS) | N comparisons | O(N) |
| Swap test | N circuit executions | O(N) |
| Mock | N comparisons | O(N) |
| Grover | floor(pi*sqrt(N)/4) oracle calls | O(sqrt(N)) |

Plot both curves against N -- the divergence is the argument for quantum search at scale. See [BENCHMARK_KPIS.md](BENCHMARK_KPIS.md) for full KPI definitions.

---

## MRR (Mean Reciprocal Rank)

Primary quality metric. Computed in `_mrr()` in `run_benchmarks.py` and `generate_report.py`.

`MRR = average of (1 / rank of first correct result) across all queries`

- Rank 1 = 1.0, rank 2 = 0.5, rank 5 = 0.2
- Harness ranks ALL images (no top-K cutoff)
- Each query maps to one correct image via `BenchmarkQuery.target_id`

> "How far does a user scroll before finding the right answer?" MRR 1.0 = always on top.

<details><summary>Self-test</summary>

**Q: Why rank ALL images instead of top-10?**
A: To measure the true rank. If the correct result is at rank 15, a top-10 cutoff would give MRR = 0, hiding useful data.
</details>

---

## Design Decisions

- **Strategy Pattern:** All engines implement `SearchEngineStrategy` (`build_index()` + `search()`) in `backend/src/engines/base.py`. Adding a new engine = implementing the interface, nothing else changes
- **Backend injection:** Quantum engines accept an optional `backend` parameter (e.g. `QiskitGroverEngine(backend=ibm_backend)`). Swap to IBM hardware without changing engine code
- **Config-driven benchmarking:** `benchmarks.yaml` controls engines, dimensions, shots, layers. Comment out a line to skip it
- **Upsert storage:** Run key `(query_id, engine_name, dimension, shots, layers)` ensures one row per config. Re-running overwrites; new params append
