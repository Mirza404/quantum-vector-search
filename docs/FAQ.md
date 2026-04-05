# Frequently Asked Questions

For full explanations of the concepts below, see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

**Q: What is this project, in plain terms?**

You type a sentence like "a dog on a beach". The system finds matching images — even though
no one manually labelled them. Both the text and the images are converted into vectors in a
shared space, and the system finds the closest vectors.

The interesting part is *how* the matching is done. A classical engine uses standard CPU math.
A quantum engine loads the vectors into a quantum circuit and measures quantum interference.
We benchmark both approaches side by side — not to claim quantum is better, but to measure
whether it works and what it costs.

---

**Q: Why does this project exist if quantum offers no speedup?**

Because "does it work?" and "is it faster?" are different questions. This project answers the
first: can the swap test match classical accuracy, and what quantum resources does it require?
That baseline is prerequisite work for evaluating quantum search when hardware improves.
See [LEARNING_ROADMAP — Part 9](LEARNING_ROADMAP.md#part-9--the-thesis-argument).

---

**Q: How does quantum parallelism differ from classical (GPU/SIMD) parallelism?**

Classical parallelism uses multiple physical units doing separate work — to cover N items you
need N/cores operations. Quantum parallelism uses superposition: one operation on n qubits
affects all 2ⁿ states simultaneously. Adding one qubit doubles the state space.

The catch: measurement collapses the superposition to a single result. You cannot read all
2ⁿ answers out. Quantum algorithms like Grover's use amplitude amplification to make the
correct answer overwhelmingly likely before measurement.
See [LEARNING_ROADMAP — Part 4.2, 4.3](LEARNING_ROADMAP.md#42-multiple-qubits).

---

**Q: What does CLIP learn?**

CLIP learns a joint embedding space from ~400M image-caption pairs via contrastive training.
It pushes matching (image, text) pairs close together and non-matching pairs apart. The result
is a general visual-semantic encoder that works on unseen data (zero-shot transfer).
See [LEARNING_ROADMAP — Part 3](LEARNING_ROADMAP.md#part-3--clip-and-embeddings).

---

**Q: What is the swap test and why does it measure similarity?**

A quantum circuit that estimates |⟨ψ|φ⟩|² — the squared cosine similarity of two
amplitude-encoded vectors. It uses a Hadamard, a CSWAP, and another Hadamard on an ancilla
qubit. The measurement probability of the ancilla encodes the similarity.
See [LEARNING_ROADMAP — Part 6.2](LEARNING_ROADMAP.md#62-the-swap-test).

---

**Q: What is amplitude encoding and what is its limitation?**

Amplitude encoding maps an n-dimensional unit vector to the amplitudes of a log₂(n)-qubit
state — exponential qubit compression. The limitation: preparing an arbitrary state requires
O(n) gates, the same cost as classical search. This is why quantum search offers no speedup
without qRAM.
See [LEARNING_ROADMAP — Part 6.1](LEARNING_ROADMAP.md#61-amplitude-encoding).

---

**Q: Why does more shots lead to higher accuracy?**

Each circuit execution returns one random bit. Estimating the true similarity requires
averaging many shots. Standard error scales as 1/√N_shots — more shots, less noise, more
accurate ranking.
See [LEARNING_ROADMAP — Part 6.3](LEARNING_ROADMAP.md#63-shot-noise).

---

**Q: What is circuit depth and why does it matter?**

The number of sequential gate layers. On real hardware, deeper circuits run longer and
accumulate more decoherence error. Current NISQ devices handle ~100 layers reliably. Circuit
depth is a proxy for hardware feasibility.
See [LEARNING_ROADMAP — Part 4.7](LEARNING_ROADMAP.md#47-circuits-depth-and-nisq).

---

**Q: What is the difference between the quantum mock engine and the Qiskit engine?**

`QuantumMockEngine` computes exact cosine similarity classically and adds synthetic noise to
simulate shot error. No quantum circuits are run. `QiskitSwapTestEngine` builds and runs real
swap test circuits on AerSimulator. The mock is fast and useful for testing; the Qiskit engine
demonstrates the actual algorithm.

---

**Q: Why is the Qiskit engine slow?**

It runs on AerSimulator, which classically simulates quantum states using 2ⁿ complex numbers.
For 15 qubits that's 32,768 amplitudes per state, times N images per query, times thousands
of shots. A real quantum chip would process all amplitudes simultaneously — the slowness is
a property of classical simulation, not the algorithm.

---

**Q: What is FAISS?**

Facebook AI Similarity Search — a library with SIMD/BLAS-optimised vector operations.
`IndexFlatL2` is its exact brute-force L2 index. For our dataset, there's no need for
approximate indices. It demonstrates a production-grade classical baseline.

---

**Q: What is MRR?**

Mean Reciprocal Rank — average of 1/(rank of first correct result) across all queries. It
measures how far a user scrolls before finding the right answer. MRR = 1.0 means the correct
answer is always first.
See [LEARNING_ROADMAP — Part 8.2](LEARNING_ROADMAP.md#82-mrr--the-quality-metric).

---

**Q: How does dataset size affect the quantum engine?**

The engine runs one circuit per image per query. Larger datasets mean more circuit executions
but the same circuit complexity (set by vector dimension, not dataset size). On a simulator
this means linear slowdown. On real hardware it would be a scheduling concern, not a
fundamental resource constraint.

---

**Q: Are the simulator results meaningful?**

Yes. AerSimulator is mathematically exact — it produces measurement statistics identical to a
perfect noiseless quantum chip. The only noise source is shot noise (statistical error from
finite measurements). Real hardware would add physical noise on top, so simulator results
represent the best-case accuracy ceiling.

---

**Q: Should we test on real IBM hardware?**

Yes, and the circuits are small enough to fit the free tier. The valuable result would be the
accuracy gap between simulator and real hardware — empirical evidence for why circuit depth
matters. Practical downside: queue times of minutes to hours.

---

**Q: What is Grover's algorithm and why can't we use it directly?**

Grover's gives O(√N) unstructured search. To use it for vector similarity search, all N
vectors must be loaded into superposition simultaneously, which requires qRAM. Without qRAM,
loading is O(N) — the speedup is cancelled. Our project runs one swap test per vector instead.
See [LEARNING_ROADMAP — Part 5](LEARNING_ROADMAP.md#part-5--grovers-algorithm).

---

**Q: Does truncating CLIP embeddings affect accuracy?**

Truncation cuts less informative components from the tail. Small reductions (512 → 128 or 64)
usually preserve rankings well. All engines receive the same truncated vectors, so truncation
does not favour one engine over another.

---

**Q: How does CLIP run locally without a GPU?**

Via PyTorch. The code auto-detects CUDA, then Apple MPS, then falls back to CPU. ViT-B/32 has
~151M parameters — small for a vision-language model. Fits in RAM, no GPU needed, no API key.

---

**Q: What do `dimensions`, `shots_values`, and `layers_values` in benchmarks.yaml control?**

- **dimensions** — vector size fed to all engines. Lower dimensions → fewer qubits, shallower
  circuits, less accuracy.
- **shots_values** — circuit executions per similarity comparison. More shots → less noise →
  more accurate but slower/costlier. Default: 512.
- **layers_values** — variational gate layers (used by `quantum_mock_sampler` only; the swap
  test engine uses a fixed circuit structure). More layers → deeper circuit → more decoherence
  risk on real hardware.

---

**Q: Would running on real IBM hardware change the conclusions?**

<<<<<<< Updated upstream
It changes practical results (more noise, accuracy gap vs simulator) but not the fundamental
constraints: no qRAM, no error correction, same O(N) limitation. The most valuable output
would be the simulator-vs-hardware accuracy gap, measured as a function of circuit depth.
=======
It changes **practical results** (more noise, accuracy gap vs simulator) but not the **fundamental constraints**: no qRAM, no error correction, same O(N) limitation. The most valuable output would be the simulator-vs-hardware accuracy gap as a function of circuit depth.

---

### What is the Strategy Pattern and why does the project use it?

All engines implement the same interface (`SearchEngineStrategy` in `backend/src/engines/base.py`): `build_index()` + `search()`. The benchmark harness iterates over engines without knowing which one is running. Adding a new engine = implementing the interface. Nothing else changes.

Same pattern for `EmbeddingGenerator` (pipeline) and `BaseDataLoader` (repository).

> **Analogy:** Like USB ports. Any device that follows the USB spec works. Any engine that implements `build_index()` + `search()` can be benchmarked.

---

### Why doesn't the app support free text search?

The app only lets users pick from **predefined queries** -- the ones in `backend/data/ground_truth.jsonc`. Each of these has a known correct answer (the target image).

With free text, we'd have no ground truth. Both engines would return results, and we'd show two lists of images side by side -- but we'd have **no way to measure which engine did better**. The user would just be eyeballing two grids with no objective comparison. Did the classical engine rank a better image first? Maybe, maybe not -- there's no correct answer to check against.

The predefined queries give us:
- **MRR** for each engine (objective accuracy number)
- **Target rank** (where the correct image landed)
- A **green highlight** on the ground-truth image so the user can visually verify

This makes the comparison scientific rather than subjective. The tradeoff is flexibility -- users can't type arbitrary queries -- but the benefit is that every search produces a meaningful, measurable result.

> **Analogy:** It's the difference between a spelling test with an answer key and a creative writing contest with no rubric. Both are valid exercises, but only one lets you objectively score the participants.
>>>>>>> Stashed changes
