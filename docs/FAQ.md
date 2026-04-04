# Frequently Asked Questions

Quick answers to the most likely exam questions. For full explanations, see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

### What is this project, in plain terms?

You type "a dog on a beach". The app finds matching images -- even though nobody manually labelled them. Both text and images are converted into 512-number lists (vectors) by CLIP, and the system finds the closest vectors.

The interesting part: **how** the matching is done. A classical engine uses standard CPU math. A quantum engine loads vectors into a quantum circuit and measures interference. We benchmark both side by side -- not to claim quantum is better, but to measure whether it works and what it costs.

> **Analogy:** Two different GPS systems trying to find the nearest restaurant. One uses Google Maps (classical). The other uses a prototype quantum GPS. We're testing whether the quantum GPS gives correct directions, not whether it's faster.

---

### Why does this project exist if quantum offers no speedup?

"Does it work?" and "Is it faster?" are different questions. This project answers the first: can the swap test match classical accuracy, and what resources does it require? That baseline is prerequisite work -- you need to know the algorithm works before you can evaluate future hardware.

See [LEARNING_ROADMAP -- Part 9](LEARNING_ROADMAP.md#part-9----the-thesis-argument).

---

### How does quantum parallelism differ from classical (GPU/SIMD) parallelism?

| | Classical | Quantum |
|---|---|---|
| **How it works** | Multiple physical units doing separate work | One operation affects all 2^n states simultaneously |
| **Scaling** | N/cores operations | Adding one qubit doubles the state space |
| **Reading results** | Read all results directly | Measurement collapses to one random result |

The catch: measurement collapses the superposition. You can't read all 2^n answers. Algorithms like Grover's use **amplitude amplification** to make the correct answer overwhelmingly likely before measurement.

See [LEARNING_ROADMAP -- Part 4.2, 4.3](LEARNING_ROADMAP.md#42-multiple-qubits).

---

### What does CLIP learn?

CLIP learns a joint embedding space from ~400M image-caption pairs via contrastive training. It pushes matching (image, text) pairs close together and non-matching pairs apart. The result: a general visual-semantic encoder that works on unseen data (**zero-shot transfer**).

**In the code:** `CLIPEmbeddingModel` in `backend/src/pipeline/clip_model.py`. For testing: `MockCLIPEmbeddingGenerator` in `backend/src/pipeline/mock_clip.py`.

See [LEARNING_ROADMAP -- Part 3](LEARNING_ROADMAP.md#part-3----clip-and-embeddings).

---

### What is the swap test and why does it measure similarity?

A quantum circuit that estimates |<psi|phi>|^2 -- the squared cosine similarity of two amplitude-encoded vectors. Uses Hadamard -> CSWAP -> Hadamard on an ancilla qubit. The measurement probability of the ancilla encodes the similarity.

**In the code:** `QiskitSwapTestEngine._run_swap_test()` in `backend/src/engines/qiskit_swaptest.py`.

See [LEARNING_ROADMAP -- Part 6.2](LEARNING_ROADMAP.md#62-the-swap-test).

---

### What is amplitude encoding and what is its limitation?

**Amplitude encoding** maps an n-dimensional unit vector to the amplitudes of log2(n) qubits -- exponential compression (64 dims -> 6 qubits).

**The limitation:** Preparing an arbitrary state requires O(n) gates, the same cost as classical search. This is why quantum search offers no speedup without qRAM.

**In the code:** `QiskitSwapTestEngine._encode()` normalises and pads to power of 2, then `circuit.initialize()` handles state preparation.

See [LEARNING_ROADMAP -- Part 6.1](LEARNING_ROADMAP.md#61-amplitude-encoding).

---

### Why does more shots lead to higher accuracy?

Each circuit execution returns one random bit. Estimating the true similarity requires averaging many shots. Standard error scales as 1/sqrt(N_shots):

| Shots | Error in P(0) |
|---|---|
| 512 | ~0.044 |
| 2048 | ~0.022 |
| 4096 | ~0.016 |

More shots, less noise, more accurate ranking. Configured in `backend/config/benchmarks.yaml` under `shots_values:`.

See [LEARNING_ROADMAP -- Part 6.3](LEARNING_ROADMAP.md#63-shot-noise).

---

### What is circuit depth and why does it matter?

The number of sequential gate layers in a quantum circuit. On real hardware, deeper circuits take longer and accumulate more **decoherence** error. Current NISQ devices handle ~100 layers reliably.

Circuit depth is a proxy for hardware feasibility. Tracked in the `circuit_depth` column of `benchmark_results` and reported in the benchmark report's "Quantum Circuit Complexity" section.

See [LEARNING_ROADMAP -- Part 4.7](LEARNING_ROADMAP.md#47-circuits-depth-and-nisq).

---

### What is the difference between the quantum mock engine and the Qiskit engine?

| | `QuantumMockEngine` | `QiskitSwapTestEngine` |
|---|---|---|
| **File** | `quantum_mock.py` | `qiskit_swaptest.py` |
| **Similarity** | Exact cosine (NumPy) + synthetic noise | Actual swap test circuit |
| **Noise** | Gaussian, stdev = layers/max(1, shots) | Real shot noise from circuit measurement |
| **Speed** | Fast (no circuits) | Slow (classical simulation of quantum states) |
| **Circuit metrics** | Theoretical estimates | Extracted from compiled Qiskit circuit |
| **Use case** | Testing, noise trade-off study | Demonstrating the actual quantum algorithm |

---

### Why is the Qiskit engine slow?

It runs on AerSimulator, which **classically simulates** quantum states using 2^n complex numbers. For 15 qubits: 32,768 amplitudes per state, times N images per query, times thousands of shots.

A real quantum chip would process all amplitudes simultaneously. The slowness is a property of **classical simulation**, not the algorithm.

---

### What is FAISS?

**Facebook AI Similarity Search** -- a library with SIMD/BLAS-optimised vector operations. `IndexFlatL2` is its exact brute-force L2 index. Demonstrates a production-grade classical baseline.

**In the code:** `FaissFlatEngine` in `backend/src/engines/faiss_flat.py` wraps `faiss.IndexFlatL2`.

---

### What is MRR?

**Mean Reciprocal Rank** -- average of 1/(rank of first correct result) across all queries. Measures how far a user scrolls before finding the right answer.

- MRR = 1.0 -> correct answer is always first
- MRR = 0.5 -> correct answer is typically second

**In the code:** `_mrr()` function in `backend/scripts/run_benchmarks.py`. The harness ranks ALL images (no top-K cutoff).

See [LEARNING_ROADMAP -- Part 8.2](LEARNING_ROADMAP.md#82-mrr----the-quality-metric).

---

### How does dataset size affect the quantum engine?

The engine runs **one circuit per image per query**. Larger datasets = more circuit executions, but **same circuit complexity** (set by vector dimension, not dataset size).

On a simulator: linear slowdown. On real hardware: a scheduling concern, not a fundamental resource constraint.

---

### Are the simulator results meaningful?

**Yes.** AerSimulator is mathematically exact -- produces measurement statistics identical to a perfect noiseless quantum chip. The only noise is **shot noise** (from finite measurements), which also exists on real hardware. Results represent the best-case accuracy ceiling.

---

### Should we test on real IBM hardware?

Yes, and our circuits (13-15 qubits) fit the free tier. The valuable result: the **accuracy gap** between simulator and real hardware -- empirical evidence for why circuit depth matters. Practical downside: queue times of minutes to hours.

---

### What is Grover's algorithm and why can't we use it directly?

Grover's gives O(sqrt(N)) unstructured search. To use it for vector search, all N vectors must be in superposition simultaneously, requiring **qRAM** (which doesn't exist). Without qRAM, loading is O(N) -- the speedup is cancelled.

Our project runs one swap test per vector instead (O(N) total, like classical). See [LEARNING_ROADMAP -- Part 5](LEARNING_ROADMAP.md#part-5----grovers-algorithm).

---

### Does truncating CLIP embeddings affect accuracy?

Truncation cuts less informative components from the tail. Small reductions (512 -> 64 or 128) usually preserve rankings well. All engines receive the same truncated vectors, so truncation doesn't favour one engine over another.

Controlled by `dimensions:` in `backend/config/benchmarks.yaml`. Truncation happens in `_prepare_vectors()` in `run_benchmarks.py`.

---

### How does CLIP run locally without a GPU?

Via PyTorch. Auto-detects CUDA -> Apple MPS -> CPU fallback (see `CLIPEmbeddingModel._resolve_device()` in `backend/src/pipeline/clip_model.py`). ViT-B/32 has ~151M parameters -- small enough for CPU. No API key needed.

---

### What do `dimensions`, `shots_values`, and `layers_values` in benchmarks.yaml control?

| Parameter | What it controls | Who uses it |
|---|---|---|
| `dimensions` | Vector size fed to all engines. Lower = fewer qubits, less accuracy | All engines |
| `shots_values` | Circuit executions per similarity comparison. More = less noise | Quantum engines only |
| `layers_values` | Variational gate layers. More = deeper circuit | `quantum_mock_sampler` only (swap test has fixed structure) |

Each combination of (engine, dimension, shots, layers) produces a separate row in `benchmark_results`.

---

### Would running on real IBM hardware change the conclusions?

It changes **practical results** (more noise, accuracy gap vs simulator) but not the **fundamental constraints**: no qRAM, no error correction, same O(N) limitation. The most valuable output would be the simulator-vs-hardware accuracy gap as a function of circuit depth.

---

### What is the Strategy Pattern and why does the project use it?

All engines implement the same interface (`SearchEngineStrategy` in `backend/src/engines/base.py`): `build_index()` + `search()`. The benchmark harness iterates over engines without knowing which one is running. Adding a new engine = implementing the interface. Nothing else changes.

Same pattern for `EmbeddingGenerator` (pipeline) and `BaseDataLoader` (repository).

> **Analogy:** Like USB ports. Any device that follows the USB spec works. Any engine that implements `build_index()` + `search()` can be benchmarked.
