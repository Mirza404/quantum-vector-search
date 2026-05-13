# Frequently Asked Questions

Quick answers to the most likely exam questions. For full explanations: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md). For the qRAM and scaling deep dive: [QUANTUM_SEARCH_ANALYSIS.md](QUANTUM_SEARCH_ANALYSIS.md).

---

### What is this project?

A text-to-image search system. You type "a dog on a beach", it finds matching images using vector similarity. Both text and images are converted to 512-dim vectors by CLIP, and the system finds the closest matches. We benchmark **five** search engines (three classical, two quantum) side-by-side to compare accuracy and cost.

---

### Why does this project exist if quantum isn't faster?

"Does it work?" and "Is it faster?" are different questions. This project answers the first: can the quantum algorithms match classical accuracy, and what resources do they need? You have to prove correctness before you can evaluate future hardware. See [QUANTUM_SEARCH_ANALYSIS.md](QUANTUM_SEARCH_ANALYSIS.md) for why this is still a valuable contribution.

---

### How does quantum parallelism differ from classical?

| | Classical (GPU/SIMD) | Quantum |
|---|---|---|
| **Mechanism** | Multiple physical units doing separate work | One operation on all 2^n states simultaneously |
| **Scaling** | Linear with hardware (N/cores) | Adding one qubit doubles the state space |
| **Reading results** | Read everything directly | Measurement collapses to one random result |

Algorithms like Grover's use **amplitude amplification** to make the correct answer overwhelmingly likely before measurement.

---

### What does CLIP do?

CLIP (OpenAI, 2021) learns a shared vector space from ~400M image-caption pairs. Similar images and descriptions end up close together, enabling text-to-image search without manual labelling (**zero-shot transfer**).

**In the code:** `CLIPEmbeddingModel` in `backend/src/pipeline/clip_model.py`. Auto-detects CUDA / MPS / CPU - runs on CPU without a GPU.

---

### What is the swap test?

A quantum circuit that estimates |<psi|phi>|^2 - the squared cosine similarity of two amplitude-encoded vectors. Uses Hadamard + CSWAP gates on an ancilla qubit. The measurement probability encodes the similarity.

**In the code:** `QiskitSwapTestEngine._run_swap_test()` in `backend/src/engines/qiskit_swaptest.py`.

---

### What is amplitude encoding?

Maps an n-dimensional vector to the amplitudes of log2(n) qubits - extreme compression (64 dims into 6 qubits). But preparing an arbitrary state takes O(n) gates - the same cost as classical search. This is why quantum search can't be faster without **qRAM**.

**In the code:** `_encode()` normalises and pads to power of 2, then `circuit.initialize()` does state preparation.

---

### What is Grover's algorithm?

An algorithm that finds a marked item in N unsorted items using O(sqrt(N)) oracle calls instead of O(N) classical comparisons. Uses repeated oracle + diffusion steps to amplify the correct answer's probability.

**The catch:** It needs all N items in quantum superposition simultaneously, which requires **qRAM** (doesn't exist). Without qRAM, loading data costs O(N), cancelling the speedup.

**In the code:** `QiskitGroverEngine` in `backend/src/engines/qiskit_grover.py`. Pre-computes the closest match classically, then runs Grover's circuit to demonstrate O(sqrt(N)) oracle scaling. See [QUANTUM_SEARCH_ANALYSIS.md](QUANTUM_SEARCH_ANALYSIS.md) for the full two-step problem explanation.

---

### Why does more shots = higher accuracy?

Each circuit run returns one random bit. Estimating true similarity requires averaging many **shots**. Standard error = 1/sqrt(N_shots):

| Shots | Error in P(0) |
|---|---|
| 512 | ~0.044 |
| 2048 | ~0.022 |
| 4096 | ~0.016 |

Configured in `backend/config/benchmarks.yaml` under `shots_values:`.

---

### What is circuit depth and why does it matter?

Number of sequential gate layers. Deeper circuits take longer and accumulate more **decoherence** (quantum noise) on real hardware. Current NISQ devices handle ~100 layers reliably. Tracked in `benchmark_results.circuit_depth`.

---

### What's the difference between the five engines?

| Engine | File | How it works | Speed |
|---|---|---|---|
| `brute_force_cosine` | `brute_force_cosine.py` | NumPy dot products | Fast. **Ground truth** |
| `faiss_flat_l2` | `faiss_flat.py` | FAISS L2 index | Fast. Production-grade |
| `faiss_hnsw_l2` | `faiss_hnsw.py` | FAISS HNSW graph index | Approximate O(log N) classical baseline |
| `qiskit_swap_test` | `qiskit_swaptest.py` | Real swap test circuit on simulator | Slow (simulation overhead) |
| `qiskit_grover` | `qiskit_grover.py` | Grover's algorithm on simulator | Slow. O(sqrt(N)) oracle scaling |

---

### Why is the Qiskit engine slow?

It runs on **AerSimulator**, which classically simulates quantum states using 2^n complex numbers. For 15 qubits: 32,768 amplitudes per state, times N images, times thousands of shots. A real quantum chip processes all amplitudes at once. The slowness is a property of **simulation**, not the algorithm.

---

### What is FAISS?

**Facebook AI Similarity Search** - a library with SIMD/BLAS-optimised vector operations. `IndexFlatL2` is its exact brute-force L2 index. Used as the production-grade classical baseline.

**In the code:** `FaissFlatEngine` in `backend/src/engines/faiss_flat.py`.

### What is HNSW?

**Hierarchical Navigable Small World** - a graph index for approximate nearest-neighbour search. It is the standard production-style classical baseline for large vector datasets: O(log N) expected query cost, with a recall trade-off that usually appears only at larger scales.

**In the code:** `FaissHnswEngine` in `backend/src/engines/faiss_hnsw.py`, wrapping `faiss.IndexHNSWFlat`.

**Benchmark caveat:** on the current 20-image dataset, HNSW is expected to match the exact FAISS L2 ranking and MRR. The approximation behaviour only becomes meaningful at thousands of vectors and above.

---

### What is MRR?

**Mean Reciprocal Rank** - average of 1/(rank of first correct result). MRR 1.0 = always first. MRR 0.5 = typically second. Evaluated over top_k results (default 10) - correct result outside top_k counts as 0.

**In the code:** `_mrr()` in `run_benchmarks.py` and `generate_report.py`.

---

### What is the operation count KPI?

The **only valid cross-engine speed comparison**. Exact classical engines do N comparisons per query, HNSW uses an approximate O(log N) graph traversal, and Grover does floor(pi*sqrt(N)/4) oracle calls. Stored in `benchmark_results.oracle_calls`.

See [BENCHMARK_KPIS.md](BENCHMARK_KPIS.md) for the full KPI specification.

---

### Do Grover benchmarks include state-preparation overhead?

No - the main Grover KPI isolates the **search step**. `qiskit_grover` pre-computes the target classically, then measures Grover's O(sqrt(N)) oracle scaling. `qiskit_grover_quantum_prep` adds quantum state-preparation circuits for target selection, but it still runs on a simulator and is not a scalable qRAM implementation.

This is intentional: the benchmark proves the Grover search subroutine behaves correctly, while the docs separately state the end-to-end limitation. Without qRAM, loading/preparing all N vectors costs O(N), which cancels the apparent O(sqrt(N)) search advantage.

---

### How do reruns avoid repeating completed benchmarks?

Each result is keyed by `(query_id, engine_name, dimension, shots, layers)`. Before a run, `run_benchmarks.py` checks `DatabaseStorage.has_record(...)`; if the row already exists, it prints `already in DB` and skips that combination. The database also enforces the same unique run key.

---

### Are simulator results meaningful?

**Yes.** AerSimulator is mathematically exact - same measurement statistics as a perfect noiseless chip. The only noise is **shot noise** (from finite measurements), which exists on real hardware too. Results represent the best-case accuracy ceiling.

---

### What about real IBM hardware?

Not used in this project. The IBM Quantum free tier is publicly accessible and our circuits (13–15 qubits) would technically fit, but two practical obstacles make it unsuitable for controlled benchmarking: queue wait times on the free tier are reported to be very long, and noise beyond roughly 7 qubits is significant enough to obscure the algorithmic signal we are measuring.

Running on real hardware is something that could be explored as a follow-up - the circuits exist and the comparison (simulator vs. hardware accuracy gap) would be interesting - but it is not a planned deliverable of this project.

---

### Does truncating CLIP embeddings hurt accuracy?

Small reductions (512 to 64 or 128) usually preserve rankings well. All engines get the same truncated vectors, so truncation doesn't favour any engine. Controlled by `dimensions:` in `benchmarks.yaml`.

---

### What do the benchmarks.yaml parameters control?

| Parameter | Controls | Used by |
|---|---|---|
| `dimensions` | Vector size fed to all engines | All engines |
| `shots_values` | Circuit executions per comparison | Quantum engines |
| `layers_values` | Required by harness, ignored by current engines | - |
| `top_k` | Results returned per query | All engines (API + benchmarks) |

Each combination produces a separate row in `benchmark_results`.

---

### What is the Strategy Pattern?

All engines implement the same interface (`SearchEngineStrategy` in `backend/src/engines/base.py`): `build_index()` + `search()`. The benchmark harness iterates over engines without knowing which one is running. Adding a new engine = implementing the interface, nothing else changes.

Same pattern for `EmbeddingGenerator` (pipeline) and `BaseDataLoader` (repository).

> Like USB ports. Any device that follows the spec works.
