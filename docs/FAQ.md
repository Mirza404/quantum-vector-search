# Frequently Asked Questions

Quick answers to the most likely exam questions. For full explanations, see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

### What is this project?

You type "a dog on a beach". The app finds matching images -- even though nobody labelled them. Both text and images are converted into 512-number lists (**vectors**) by CLIP, and the system finds the closest ones.

The twist: **how** the matching is done. A classical engine uses CPU math. A quantum engine loads vectors into a quantum circuit and measures interference. We benchmark both -- not to claim quantum is better, but to measure whether it works and what it costs.

> **Analogy:** Two GPS systems finding the nearest restaurant. One uses Google Maps (classical). The other uses a prototype quantum GPS. We're testing whether the quantum GPS gives correct directions, not whether it's faster.

---

### Why does this project exist if quantum isn't faster?

"Does it work?" and "Is it faster?" are different questions. This project answers the first: can the swap test match classical accuracy, and what resources does it need? You have to prove the algorithm works before you can evaluate future hardware.

---

### How does quantum parallelism differ from classical?

| | Classical (GPU/SIMD) | Quantum |
|---|---|---|
| **Mechanism** | Multiple physical units doing separate work | One operation on all 2^n states simultaneously |
| **Scaling** | N/cores operations | Adding one qubit doubles the state space |
| **Reading results** | Read everything directly | Measurement collapses to one random result |

The catch: you can't read all 2^n answers. Algorithms like Grover's use **amplitude amplification** to make the correct answer overwhelmingly likely before measurement.

---

### What does CLIP learn?

CLIP learns a shared embedding space from ~400M image-caption pairs. It pushes matching pairs close together and non-matching pairs apart. The result: a general visual-semantic encoder that works on images it's never seen (**zero-shot transfer**).

**In the code:** `CLIPEmbeddingModel` in `backend/src/pipeline/clip_model.py`. For testing: `MockCLIPEmbeddingGenerator` in `mock_clip.py`.

---

### What is the swap test?

A quantum circuit that estimates \|<psi\|phi>\|^2 -- the squared cosine similarity of two amplitude-encoded vectors. Uses Hadamard + CSWAP gates on an ancilla qubit. The measurement probability encodes the similarity.

**In the code:** `QiskitSwapTestEngine._run_swap_test()` in `backend/src/engines/qiskit_swaptest.py`.

---

### What is amplitude encoding and its limitation?

**Amplitude encoding** maps an n-dimensional vector to the amplitudes of log2(n) qubits -- extreme compression (64 dims into 6 qubits). But preparing an arbitrary state takes O(n) gates -- the same cost as classical search. This is why quantum search can't be faster without **qRAM**.

**In the code:** `QiskitSwapTestEngine._encode()` normalises and pads to power of 2, then `circuit.initialize()` prepares the state.

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

### What is circuit depth?

The number of sequential gate layers in a circuit. Deeper circuits take longer and accumulate more **decoherence** error on real hardware. Current NISQ devices handle ~100 layers reliably.

Tracked in `benchmark_results.circuit_depth` and reported in the benchmark report's "Quantum Circuit Complexity" section.

---

### Quantum mock engine vs. Qiskit engine?

| | `QuantumMockEngine` | `QiskitSwapTestEngine` |
|---|---|---|
| **File** | `quantum_mock.py` | `qiskit_swaptest.py` |
| **Similarity** | Exact cosine + synthetic noise | Actual swap test circuit |
| **Speed** | Fast (no circuits) | Slow (classical simulation) |
| **Use case** | Noise trade-off study | Demonstrating the real algorithm |

---

### Why is the Qiskit engine slow?

It runs on **AerSimulator**, which classically simulates quantum states using 2^n complex numbers. For 15 qubits: 32,768 amplitudes per state, times N images, times thousands of shots. A real quantum chip would process all amplitudes at once. The slowness is a property of **simulation**, not the algorithm.

---

### What is FAISS?

**Facebook AI Similarity Search** -- a library with SIMD/BLAS-optimised vector operations. `IndexFlatL2` is its exact brute-force L2 index. Used as the production-grade classical baseline.

**In the code:** `FaissFlatEngine` in `backend/src/engines/faiss_flat.py`.

---

### What is MRR?

**Mean Reciprocal Rank** -- average of 1/(rank of first correct result). MRR 1.0 = always first. MRR 0.5 = typically second. The harness ranks ALL images (no top-K cutoff).

**In the code:** `_mrr()` in `backend/scripts/run_benchmarks.py`.

---

### How does dataset size affect the quantum engine?

One circuit per image per query. Larger datasets = more circuit runs, but **same circuit complexity** (set by vector dimension, not dataset size). On a simulator: linear slowdown. On real hardware: a scheduling concern, not a fundamental resource problem.

---

### Are simulator results meaningful?

**Yes.** AerSimulator is mathematically exact -- same measurement statistics as a perfect noiseless chip. The only noise is **shot noise** (from finite measurements), which exists on real hardware too. Results represent the best-case accuracy ceiling.

---

### What about real IBM hardware?

Our circuits (13-15 qubits) fit the free tier. The most valuable result would be the **accuracy gap** between simulator and real hardware -- empirical evidence for why circuit depth matters. Practical downside: queue times of minutes to hours.

---

### What is Grover's algorithm and why can't we use it?

**Grover's** gives O(sqrt(N)) unstructured search. To use it for vector search, all N vectors must be in superposition simultaneously -- requiring **qRAM** (which doesn't exist). Without it, loading is O(N), cancelling the speedup.

Our project runs one swap test per vector instead (O(N) total, like classical).

---

### Does truncating CLIP embeddings hurt accuracy?

Small reductions (512 to 64 or 128) usually preserve rankings well. All engines get the same truncated vectors, so truncation doesn't favour any engine.

Controlled by `dimensions:` in `backend/config/benchmarks.yaml`. Done in `_prepare_vectors()` in `run_benchmarks.py`.

---

### What do the benchmarks.yaml parameters control?

| Parameter | Controls | Used by |
|---|---|---|
| `dimensions` | Vector size fed to all engines | All engines |
| `shots_values` | Circuit executions per comparison | Quantum engines only |
| `layers_values` | Variational gate layers | `quantum_mock_sampler` only |

Each combination produces a separate row in `benchmark_results`.

---

### What is the Strategy Pattern?

All engines implement the same interface (`SearchEngineStrategy` in `backend/src/engines/base.py`): `build_index()` + `search()`. The benchmark harness iterates over engines without knowing which one is running. Adding a new engine = implementing the interface.

Same pattern for `EmbeddingGenerator` (pipeline) and `BaseDataLoader` (repository).

> **Analogy:** Like USB ports. Any device that follows the spec works.
