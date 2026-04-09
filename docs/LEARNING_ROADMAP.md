# Learning Roadmap

Everything you need to understand this project -- from basic math to quantum circuits to the thesis argument. This is the primary learning document; other docs reference it.

**Who this is for:** Someone who can write code but has never studied quantum physics.

**How to read:** Straight through. Each part builds on the previous one.

---

## Part 1 -- The Math

You need four concepts.

### 1.1 Vectors

A **vector** is an ordered list of numbers: `v = (v1, v2, ..., vn)`. In this project, vectors represent meaning. CLIP converts a sentence into 512 numbers, and an image into another 512 numbers. If the sentence describes the image, those lists end up similar.

> **Analogy:** GPS coordinates, but 512 dimensions instead of 2. Each dimension captures some aspect of meaning. Similar meanings = nearby locations.

### 1.2 Dot Product

Multiply corresponding components, sum them: `a . b = a1*b1 + a2*b2 + ... + an*bn`

- **Large positive** = same direction = similar meaning
- **Near zero** = perpendicular = unrelated
- **Negative** = opposite

### 1.3 L2 Norm and Normalisation

- **L2 norm** (length): `||v|| = sqrt(v1^2 + v2^2 + ... + vn^2)`
- **Normalisation** divides by length, giving a **unit vector** (length = 1)
- This project normalises everything first (see `CLIPEmbeddingModel.encode_texts()` and `encode_images()` -- both use `torch.nn.functional.normalize`)
- After normalisation, cosine similarity, dot product, and L2 distance all give the **same ranking**

### 1.4 Cosine Similarity

`cos(theta) = (a . b) / (||a|| * ||b||)` -- ranges from -1 (opposite) to +1 (identical direction).

On unit vectors: **cosine = dot product**. The swap test (Part 6) computes |a . b|^2 -- same quantity, squared. The squaring means it can't tell +0.8 from -0.8, but CLIP vectors cluster on the positive side, so this is fine.

**In one sentence:** Normalise the vectors, then a dot product tells you how similar two things are.

<details><summary>Self-test</summary>

**Q: Why normalise vectors before comparing them?**
A: So cosine, dot product, and L2 all give the same ranking -- and so vectors satisfy the quantum requirement that amplitudes squared sum to 1.

**Q: Cosine similarity of a unit vector with itself?**
A: 1.0.
</details>

---

## Part 2 -- Classical Search

### 2.1 The Problem

Given a query vector q and N database vectors, find the K most similar. This is **k-nearest-neighbour (kNN)**.

### 2.2 Brute Force

Compare q against every vector. N dot products, sort, return top K.
- **Cost:** O(N * d) per query
- **Accuracy:** Perfect -- always finds true nearest neighbours
- **In the code:** `BruteForceCosineEngine` in `backend/src/engines/brute_force_cosine.py` -- uses `self._matrix @ query`

> **Analogy:** Finding the tallest person by measuring everyone. Guaranteed correct, but slow in a big crowd.

### 2.3 FAISS

Same brute-force logic but with Facebook's FAISS library (SIMD-optimised). Still exact, but faster in practice. Uses L2 distance -- same ranking on normalised vectors.
- **In the code:** `FaissFlatEngine` in `backend/src/engines/faiss_flat.py`, wraps `faiss.IndexFlatL2`

### 2.4 HNSW (Approximate)

For large datasets, brute force is slow. **HNSW** (Hierarchical Navigable Small World) builds a multi-layer graph for O(log N) search. Trade-off: might miss the exact nearest neighbour.

pgvector uses HNSW for `image_vectors` (see `db/migrations/up/1_initial_schema.sql`). For ~20 images, brute force is fine; HNSW matters at thousands+ vectors.

> **Analogy:** Looking up a word in a dictionary -- you jump to roughly the right section, then narrow down. Much faster, might land one page off.

**In one sentence:** Classical search either compares against every vector (brute force) or uses indexing (HNSW) to skip most comparisons.

<details><summary>Self-test</summary>

**Q: Why include both `brute_force_cosine` and `faiss_flat_l2` if they give the same results?**
A: Brute-force is a simple baseline. FAISS demonstrates a production-grade implementation.

**Q: Why not use HNSW for benchmarking?**
A: HNSW is approximate. Benchmarking needs exact results to fairly measure MRR.
</details>

---

## Part 3 -- CLIP and Embeddings

### 3.1 What Is an Embedding?

A function that converts input (text, image) into a fixed-length vector, trained so similar inputs map to nearby vectors.

> **Analogy:** A sommelier assigning flavour profile scores to every wine. Similar wines get similar scores. The scores ARE the embedding.

### 3.2 CLIP

**CLIP** (Contrastive Language-Image Pre-training, OpenAI 2021) has two encoders:
- **Image encoder** (ViT-B/32): 224x224 image -> 512-dim vector
- **Text encoder** (Transformer): text -> 512-dim vector

The key: **both output into the same space**. A photo of a dog and "a dog on a beach" end up near each other. This makes cross-modal search possible.

**In the code:** `CLIPEmbeddingModel` in `backend/src/pipeline/clip_model.py`. `encode_texts()` for text, `encode_images()` for images. For testing: `MockCLIPEmbeddingGenerator` in `mock_clip.py` (deterministic pseudo-random vectors via SHA-256).

### 3.3 Training

Trained on ~400M image-caption pairs. For each batch, CLIP builds a similarity matrix -- pushes correct pairs toward 1, wrong pairs toward 0. Result: a model that understands visual and semantic concepts on images it's never seen (**zero-shot transfer**).

### 3.4 Truncation and Normalisation

- CLIP outputs 512 dims. The project **truncates** to smaller sizes (64, 128) to study accuracy vs. quantum cost
- Configured in `benchmarks.yaml` under `dimensions:`, applied in `_prepare_vectors()` in `run_benchmarks.py`
- **Normalisation** is required for two reasons: (1) makes all similarity metrics equivalent, (2) quantum amplitude encoding needs squared amplitudes summing to 1

**In one sentence:** CLIP puts text and images into the same 512-number space; we normalise and optionally truncate before feeding to any engine.

<details><summary>Self-test</summary>

**Q: Why can we search for images using text?**
A: CLIP maps both into the same vector space. Similar meanings = nearby vectors.

**Q: What does `MockCLIPEmbeddingGenerator` do?**
A: Generates deterministic pseudo-random vectors from text via SHA-256 hash. For testing without loading the real CLIP model.
</details>

---

## Part 4 -- Quantum Computing Essentials

### 4.1 Qubits

A classical bit is 0 or 1. A **qubit** can be in **superposition**: `|psi> = alpha|0> + beta|1>`

- alpha and beta are **amplitudes** (complex numbers), constrained by |alpha|^2 + |beta|^2 = 1
- **Measurement** gives 0 with probability |alpha|^2, or 1 with probability |beta|^2
- Before measurement, amplitudes **interfere** -- this is what makes quantum algorithms work

> **Analogy:** A classical bit is a light switch (on/off). A qubit is a dial on a sphere. When you look (measure), it snaps to on or off, with probabilities set by the dial position.

### 4.2 Multiple Qubits

n qubits = 2^n states in superposition simultaneously. One operation affects all states at once -- **quantum parallelism**.

| Qubits | States |
|---|---|
| 10 | 1,024 |
| 20 | ~1 million |
| 50 | ~10^15 |

> **Analogy:** Classical parallelism = hiring more workers. Quantum parallelism = one worker in multiple realities, doing a different task in each. But you can only ask one reality for its answer.

### 4.3 Interference

When paths through a circuit lead to the same state, amplitudes add:
- Same sign = **constructive** (probability increases)
- Opposite signs = **destructive** (probability decreases)

Every quantum algorithm engineers the circuit so wrong answers cancel and the right answer amplifies.

### 4.4 Gates

Gates are operations on qubits -- always **unitary** (reversible, preserves total probability).

| Gate | Qubits | What it does | Used in |
|---|---|---|---|
| **Hadamard (H)** | 1 | Equal superposition: H\|0> = (\|0>+\|1>)/sqrt(2) | Swap test ancilla |
| **CNOT** | 2 | Flips target if control is \|1> | General circuits |
| **CSWAP (Fredkin)** | 3 | Swaps two targets if control is \|1> | Swap test core |

### 4.5 Entanglement

When qubits interact through gates, their states become **entangled** -- can't be described separately. Measuring one immediately determines the other.

> **Analogy:** Magic dice -- roll one, get 6, the other is guaranteed 6, no matter the distance. Not communication -- they were entangled from the start.

### 4.6 Measurement

Measuring forces a definite state. You **cannot** read all 2^n amplitudes -- one measurement gives one result. Algorithms must make the correct answer high-amplitude before measuring.

### 4.7 Circuit Depth and NISQ

- **Circuit depth** = sequential gate layers (parallel gates count as one)
- Real qubits lose coherence over time (**decoherence**) -- deeper circuits = more error
- **NISQ** (Noisy Intermediate-Scale Quantum) = current era. Reliable depth: ~100 layers

This project tracks circuit depth in `benchmark_results.circuit_depth` because it directly predicts hardware feasibility.

**In one sentence:** Qubits hold superpositions, gates manipulate them, measurement collapses to one answer, and circuit depth determines if real hardware can run it.

<details><summary>Self-test</summary>

**Q: Why can't you read all 2^n amplitudes from a quantum register?**
A: Measurement collapses the superposition to one random result. You need many shots to learn about the amplitudes.

**Q: What limits current quantum hardware?**
A: Circuit depth. NISQ devices handle ~100 gate layers before noise dominates.
</details>

---

## Part 5 -- Grover's Algorithm

### 5.1 The Promise

Find one matching item in an unsorted database of N items:
- **Classical:** O(N) -- check every item
- **Grover's (1996):** O(sqrt(N)) -- provably optimal

For 1,000,000 items: classical ~1M checks, Grover's ~1,000.

### 5.2 How It Works

1. **Initialise:** Hadamard on all qubits -> uniform superposition
2. **Repeat ~(pi/4)*sqrt(N) times:**
   - **Oracle:** Flips the sign of the target's amplitude
   - **Diffusion:** Reflects all amplitudes around the mean -- the target bounces above everyone else
3. **Measure:** Target now has amplitude ~1

> **Analogy:** Everyone standing at the same height on a trampoline. The oracle pushes the target below the surface. Diffusion flips the trampoline -- the pushed person is now highest. Repeat until they tower over everyone.

### 5.3 Why This Doesn't Help Our Project

Grover's needs all N vectors in superposition simultaneously, requiring **qRAM** -- a theoretical device that loads N vectors in O(log N) steps. **qRAM does not exist.**

Without it, loading each vector costs O(n) gates. Loading all N vectors = O(N*n) -- **worse than classical**.

So `QiskitSwapTestEngine` runs one circuit per database vector, N times total. O(N) overall. The quantum part is only the similarity computation, not the search.

**This is one of the project's key findings:** the theoretical O(sqrt(N)) speedup is blocked by state preparation cost.

**In one sentence:** Grover's could search in sqrt(N) time, but needs qRAM to load data -- so our project does O(N) search with quantum similarity computation.

<details><summary>Self-test</summary>

**Q: What prerequisite does Grover's need that we don't have?**
A: qRAM -- quantum memory that loads all N vectors into superposition in O(log N) time.

**Q: What does the quantum engine actually do without Grover's?**
A: Runs one swap test per database image, comparing each to the query individually. Quantum similarity, classical search.
</details>

---

## Part 6 -- Amplitude Encoding and the Swap Test

The core quantum technique in this project.

### 6.1 Amplitude Encoding

To use a quantum circuit, vectors must become quantum states. **Amplitude encoding** maps vector components to qubit amplitudes:

```
|psi_v> = v1|00...0> + v2|00...1> + ... + vn|11...1>
```

**Compression:** 64 dims = 6 qubits (2^6 = 64). But preparing an arbitrary state takes O(n) gates -- the bottleneck that cancels Grover's speedup.

> **Analogy:** Storing a 64-page book in a 6-digit code. Incredibly compact, but writing the code takes as long as reading the book.

**In the code:** `QiskitSwapTestEngine._encode()` normalises and pads to power of 2, then `circuit.initialize()` in `_run_swap_test()` does state preparation.

### 6.2 The Swap Test

Estimates |<psi|phi>|^2 -- squared cosine similarity on unit vectors.

**Circuit:**
```
ancilla: |0> --H--*--H--M
                  |
state psi:       --X--     (CSWAP)
state phi:       --X--
```

1. Load query and database vector via amplitude encoding
2. Hadamard on ancilla (superposition)
3. CSWAP: if ancilla is |1>, swap the two registers
4. Hadamard on ancilla again
5. Measure ancilla: P(0) = (1 + |<psi|phi>|^2) / 2

**In the code:** `QiskitSwapTestEngine._run_swap_test()` in `backend/src/engines/qiskit_swaptest.py`.

**Why squared?** The swap test gives |<psi|phi>|^2, not signed similarity. Can't distinguish +0.8 from -0.8. For CLIP embeddings (positive side), this doesn't matter.

### 6.3 Shot Noise

Each circuit run returns one bit (0 or 1). To estimate P(0), run many **shots**:

```
P(0) ~ (count of 0s) / N_shots
standard error ~ 1 / sqrt(N_shots)
```

| Shots | Std error in P(0) |
|---|---|
| 512 | ~0.044 |
| 2048 | ~0.022 |
| 4096 | ~0.016 |

The `quantum_mock_sampler` simulates this: exact cosine + Gaussian noise scaled by `layers / max(1, shots)` (see `QuantumMockEngine.search()` in `quantum_mock.py`).

**In one sentence:** Each shot gives one bit of information; more shots average out randomness to reveal the true similarity.

<details><summary>Self-test</summary>

**Q: How does the swap test measure similarity?**
A: Quantum interference between encoded vectors. Similar vectors = constructive interference (ancilla likely 0). Different = destructive (ancilla ~50/50).

**Q: Why does the mock engine add noise as layers/shots?**
A: More layers = deeper circuit = more noise. More shots = better averaging = less noise. The ratio captures this without running actual circuits.
</details>

---

## Part 7 -- The qRAM Problem

### 7.1 What qRAM Would Do

**qRAM** would take a superposition of indices and return a superposition of data -- loading the entire database in O(log N) steps. Combined with Grover's: O(sqrt(N)) search.

Without it: encoding each vector = O(n) gates, all N vectors = O(N*n) -- worse than classical.

> **Analogy:** A library where you manually copy each book to check it (O(N)). qRAM = a magic librarian who checks all books simultaneously.

### 7.2 The Key Finding

The algorithm works (this project proves it). The bottleneck is data loading. The project measures per-circuit resource cost (depth, qubits, shots) to establish exactly what's needed when qRAM becomes available.

### 7.3 Current Hardware

- IBM chips: 1000+ physical qubits, reliable depth ~100
- **Quantum error correction** encodes one logical qubit using 50-1000 physical qubits -- current hardware can't afford this overhead
- This project uses **AerSimulator** -- mathematically exact, no hardware noise, but exponentially expensive in classical memory (n qubits = 2^n complex numbers)

**In one sentence:** qRAM would unlock quantum speedup, but doesn't exist yet; the project measures everything else so the baseline is ready.

<details><summary>Self-test</summary>

**Q: What's the fundamental bottleneck?**
A: State preparation costs O(n) gates -- same as classical. qRAM would reduce this to O(log N).

**Q: Why are AerSimulator results meaningful?**
A: Mathematically exact -- same statistics as a perfect noiseless chip. Shot noise is real (also present on hardware). Results are the best-case ceiling.
</details>

---

## Part 8 -- Engines and Metrics

### 8.1 The Four Engines

All implement `SearchEngineStrategy` (`build_index()` + `search()`) in `backend/src/engines/base.py`.

| Engine | File | What it does |
|---|---|---|
| **BruteForceCosineEngine** | `brute_force_cosine.py` | NumPy dot products. Exact. **Ground truth baseline** |
| **FaissFlatEngine** | `faiss_flat.py` | FAISS SIMD-optimised L2. Exact. Production-grade |
| **QuantumMockEngine** | `quantum_mock.py` | Exact cosine + Gaussian noise. No circuits. Fast noise study |
| **QiskitSwapTestEngine** | `qiskit_swaptest.py` | Real swap test on AerSimulator. **Actual quantum computation** |

> **Analogy:** Four chefs cooking the same dish. Two use standard recipes. One pretends to use a quantum oven but adds random salt. One actually uses the quantum oven. We taste-test all four.

### 8.2 MRR

**Mean Reciprocal Rank** -- each query has one correct image. The engine ranks all images.

```
MRR = average of (1 / rank of correct image) across all queries
```

| Rank | Score |
|---|---|
| 1st | 1.0 |
| 2nd | 0.5 |
| 5th | 0.2 |

The harness ranks ALL images (no top-K cutoff -- `top_k=len(dataset_ids)` in `run_benchmarks.py`). Each query maps to one correct image via `BenchmarkQuery.target_id` (strips `query_` prefix).

### 8.3 Quantum Metrics

| Metric | Measures | Why it matters |
|---|---|---|
| **Circuit depth** | Sequential gate layers | Decoherence risk proxy |
| **Qubit count** | Qubits per swap test | Hardware allocation |
| **Shots vs. MRR** | Quality at different budgets | Cost on real hardware |

### 8.4 Why Speed Isn't Compared Across Engines

The quantum engine runs on a classical simulator -- its timing reflects simulating 2^n amplitudes on CPU, not real quantum speed. **MRR is valid across engines. Speed is only valid within one engine across dimensions.**

**In one sentence:** Four interchangeable engines let us compare quantum accuracy against classical, while tracking qubits, depth, and shots as cost metrics.

<details><summary>Self-test</summary>

**Q: Why is brute-force cosine the ground truth?**
A: Simplest, most transparent exact implementation. FAISS gives the same ranking but is less transparent.

**Q: Why can't we compare speed across engines?**
A: Qiskit timing reflects simulation overhead, not real quantum hardware speed.
</details>

---

## Part 9 -- The Thesis Argument

The full argument, end to end:

1. **Grover's algorithm** gives O(sqrt(N)) quantum search -- a proven quadratic speedup
2. Applying it to vector search requires **amplitude encoding**, which costs **O(n) gates per vector** -- same as classical. Speedup cancelled
3. **qRAM** could fix this (load all vectors in O(log N)). qRAM doesn't exist
4. The **swap test** accurately estimates cosine similarity on AerSimulator, matching classical MRR with enough shots
5. **Circuit depth and qubit count** are measured from actual compiled Qiskit circuits, giving concrete hardware requirements
6. **Conclusion:** The quantum approach is correct but blocked by state preparation cost. The project provides the accuracy baseline, resource model, and framework needed to re-evaluate when hardware improves

**What we are NOT claiming:** That quantum is faster, or that it will be. We prove the algorithm works, measure what it costs, and identify what needs to change (qRAM).

> **How to frame at a defense:** "We proved the algorithm works under ideal conditions, measured what it costs on real hardware, and identified the specific missing technology (qRAM) that prevents practicality. Our framework is a ready-made baseline for when quantum hardware catches up."

<details><summary>Self-test</summary>

**Q: Summarise the thesis in one sentence.**
A: The quantum swap test correctly performs cross-modal vector search on a simulator, but state preparation cost prevents speedup until qRAM becomes available.

**Q: Three contributions of this project?**
A: (1) Empirical proof the swap test works, (2) measured circuit depth and qubit counts per dimension, (3) a benchmarking framework ready for future hardware.

**Q: Most common examiner misconception?**
A: That the project claims quantum is faster. It doesn't -- it measures correctness and cost.
</details>
