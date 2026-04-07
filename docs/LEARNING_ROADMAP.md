# Learning Roadmap

Everything you need to understand this project -- from the math to the quantum circuits to the thesis argument. This is the primary learning document. Other docs reference this one.

**Who this is for:** A CS student who can write code but has never studied quantum physics.

**How to read it:** Straight through, in order. Each part builds on the previous one.

---

## Part 1 -- The Math

You need four concepts. That's it.

### 1.1 Vectors

A **vector** is an ordered list of numbers: `v = (v1, v2, ..., vn)`

In this project, vectors represent meaning. CLIP converts a sentence into 512 numbers, and converts an image into a different 512 numbers. If the sentence describes the image, those two lists end up similar.

> **Analogy:** Think of a vector as GPS coordinates, but instead of 2 dimensions (latitude, longitude), you have 512 dimensions. Each dimension captures some aspect of meaning. Things with similar meanings end up at nearby "locations."

### 1.2 Dot Product

Multiply each pair of corresponding components, sum them up:

```
a . b = a1*b1 + a2*b2 + ... + an*bn
```

- **Large positive** -> vectors point the same direction -> similar meaning
- **Near zero** -> perpendicular -> unrelated
- **Negative** -> opposite directions -> opposite meaning

### 1.3 L2 Norm and Normalisation

The **L2 norm** (length) of a vector: `||v|| = sqrt(v1^2 + v2^2 + ... + vn^2)`

**Normalisation** divides a vector by its length, making it a **unit vector** (length = 1): `v_normalised = v / ||v||`

This project normalises all vectors before anything else (see `CLIPEmbeddingModel.encode_texts()` and `encode_images()` -- both use `torch.nn.functional.normalize`). After normalisation, all three similarity metrics become equivalent.

### 1.4 Cosine Similarity

Measures the angle between two vectors:

```
cos(theta) = (a . b) / (||a|| * ||b||)
```

Ranges from -1 (opposite) to +1 (identical direction). After normalisation (both have length 1), this simplifies to: `cos(theta) = a . b`

So on unit vectors, **cosine similarity = dot product**. That's why we normalise.

**Why this matters for quantum:** The swap test (Part 6) computes |a . b|^2 -- the **squared** dot product. Same quantity, different method. The squaring means it can't tell positive from negative similarity, but for CLIP vectors (which cluster on the same side), this is fine.

**In one sentence:** Normalise the vectors, then a simple dot product tells you how similar two things are.

<details>
<summary>Self-test</summary>

**Q: Why does this project normalise vectors before comparing them?**
A: So that cosine similarity, dot product, and L2 distance all give the same ranking -- and so vectors meet the quantum requirement that amplitudes squared sum to 1.

**Q: What's the cosine similarity of a vector with itself (after normalisation)?**
A: 1.0 (the dot product of a unit vector with itself is 1).
</details>

---

## Part 2 -- Classical Search

### 2.1 The Problem

Given a query vector q and N database vectors, find the K most similar vectors. This is the **k-nearest-neighbour (kNN)** problem.

### 2.2 Brute Force

Compare q against every vector. Compute N dot products, sort by score, return top K.

- **Cost:** O(N * d) per query (N = dataset size, d = vector dimension)
- **Accuracy:** Perfect -- always finds the true nearest neighbours
- **In the code:** `BruteForceCosineEngine` in `backend/src/engines/brute_force_cosine.py`. Uses NumPy matrix multiplication: `scores = self._matrix @ query`

> **Analogy:** Finding the tallest person in a room by measuring everyone's height. Guaranteed correct, but slow if the room has a million people.

### 2.3 FAISS IndexFlatL2

Same brute-force logic, but using Facebook's FAISS library with hardware-level CPU optimisations (SIMD instructions). Still O(N * d), still exact, but faster in practice.

- Uses L2 distance instead of cosine, but on normalised vectors the ranking is identical
- **In the code:** `FaissFlatEngine` in `backend/src/engines/faiss_flat.py`. Wraps `faiss.IndexFlatL2`

### 2.4 HNSW (Approximate Search)

For large datasets, brute force is too slow. **HNSW** (Hierarchical Navigable Small World) builds a multi-layer graph:

- **Upper layers:** Few nodes, long-range connections -- fast coarse navigation
- **Lower layers:** Many nodes, short-range connections -- precise local search

**Cost:** O(log N) per query. **Trade-off:** Might miss the exact nearest neighbour.

pgvector uses HNSW for the `image_vectors` table (see `db/migrations/up/1_initial_schema.sql`). For our ~20-image dataset, brute force is fine. HNSW matters at thousands+ vectors.

> **Analogy:** Looking up a word in a dictionary. You don't read every page -- you jump to roughly the right section, then narrow down. Much faster, but you might land one page off.

**In one sentence:** Classical search compares the query against every vector (brute force) or uses clever indexing (HNSW) to skip most comparisons.

<details>
<summary>Self-test</summary>

**Q: Why does the project include both `brute_force_cosine` and `faiss_flat_l2` if they give the same results?**
A: `brute_force_cosine` is a simple, transparent baseline. `faiss_flat_l2` demonstrates a production-grade implementation. Both are exact but FAISS is faster on large data.

**Q: Why is HNSW not used for benchmarking?**
A: Because HNSW is approximate -- it might miss the true nearest neighbour. Benchmarking needs exact results to fairly measure MRR.
</details>

---

## Part 3 -- CLIP and Embeddings

### 3.1 What Is an Embedding?

An **embedding** is a function that converts input (text, image, audio) into a fixed-length vector. The function is trained so that similar inputs map to nearby vectors.

> **Analogy:** A sommelier who assigns a flavour profile score (fruity, oaky, acidic...) to every wine. Wines that taste similar get similar scores. The scores ARE the embedding.

### 3.2 CLIP

**CLIP** (Contrastive Language-Image Pre-training, OpenAI 2021) has two encoders trained together:

- **Image encoder** -- a Vision Transformer (ViT-B/32). Takes a 224x224 image, splits into 32x32 patches, outputs a 512-dim vector
- **Text encoder** -- a Transformer. Takes text, outputs a 512-dim vector

The critical property: **both encoders output into the same 512-dimensional space.** A photo of a dog and the text "a dog on a beach" end up near each other. This is what makes cross-modal search possible.

**In the code:** `CLIPEmbeddingModel` in `backend/src/pipeline/clip_model.py`. `encode_texts()` for text, `encode_images()` for images. For testing without the real CLIP model, there's `MockCLIPEmbeddingGenerator` in `backend/src/pipeline/mock_clip.py`.

### 3.3 How CLIP Was Trained

Trained on ~400M image-caption pairs. For each batch of N pairs, CLIP builds an NxN similarity matrix. The loss function:
- Pushes the N correct (image, caption) pairs toward similarity 1
- Pushes the N^2 - N wrong pairs toward 0

The result: a model that understands general visual and semantic concepts, even on images it has never seen (**zero-shot transfer**).

### 3.4 Why We Truncate Vectors

CLIP outputs 512 dimensions. The project truncates to smaller sizes (e.g. 64, 128) to study how dimension affects accuracy and quantum cost. Configured in `backend/config/benchmarks.yaml` under `dimensions:`.

- Truncation keeps the **first d components** (which carry the most information)
- Happens in `_prepare_vectors()` in `backend/scripts/run_benchmarks.py`
- All engines receive the same truncated vectors, so truncation doesn't favour any engine

### 3.5 Why Normalisation Is Required

Two reasons:
1. **Classical search:** On unit vectors, cosine = dot product = monotonically related to L2. All metrics give the same ranking
2. **Quantum search:** Amplitude encoding requires squared amplitudes to sum to 1. A unit vector satisfies this automatically

**In one sentence:** CLIP converts text and images into the same kind of 512-number summary, and we normalise + truncate these before feeding them to any search engine.

<details>
<summary>Self-test</summary>

**Q: Why can we search for images using text?**
A: Because CLIP puts both into the same vector space. "Dog on beach" (text) and a photo of a dog on a beach produce similar 512-dim vectors.

**Q: What does `MockCLIPEmbeddingGenerator` do?**
A: Generates deterministic pseudo-random vectors from text (using SHA-256 hash as seed). Used for testing without loading the real CLIP model.
</details>

---

## Part 4 -- Quantum Computing Essentials

### 4.1 Qubits

A classical bit is 0 or 1. A **qubit** can be in a **superposition** of both:

```
|psi> = alpha|0> + beta|1>
```

- `|0>` and `|1>` are the two basis states (bra-ket notation -- just a convention)
- alpha and beta are **amplitudes** (complex numbers)
- Constraint: |alpha|^2 + |beta|^2 = 1
- When you **measure**, you get 0 with probability |alpha|^2 and 1 with probability |beta|^2

> **Analogy:** A classical bit is a light switch (on or off). A qubit is more like a dial that can point anywhere on a sphere. When you look at it (measure), it snaps to either "on" or "off", but with probabilities determined by where the dial was pointing.

The key insight: before measurement, amplitudes **interfere** with each other. This is the mechanism that makes quantum algorithms work.

### 4.2 Multiple Qubits

n qubits have 2^n possible states, all in superposition simultaneously:

```
|psi> = alpha_0|00...0> + alpha_1|00...1> + ... + alpha_{2^n-1}|11...1>
```

| Qubits | Simultaneous states |
|---|---|
| 10 | 1,024 |
| 20 | ~1 million |
| 50 | ~10^15 |

One operation on this register affects **all 2^n states at once**. That is **quantum parallelism**.

> **Analogy:** Classical parallelism is hiring more workers -- 10 workers do 10 tasks. Quantum parallelism is more like a single worker who exists in multiple realities simultaneously, doing a different task in each one. But you can only ask one reality for its answer.

### 4.3 Interference

When different paths through a circuit lead to the same state, their amplitudes **add**:
- Same sign -> **constructive** interference -> probability increases
- Opposite signs -> **destructive** interference -> probability decreases

Every quantum algorithm works by engineering the circuit so wrong answers cancel out and the right answer amplifies.

### 4.4 Quantum Gates

Gates are operations on qubits. Every gate is **unitary** (reversible, preserves total probability).

The gates used in this project:

| Gate | Qubits | What it does | Used in |
|---|---|---|---|
| **Hadamard (H)** | 1 | Creates equal superposition. H\|0> = (\|0> + \|1>)/sqrt(2) | Swap test (ancilla) |
| **CNOT** | 2 | Flips target if control is \|1>. Creates entanglement | General circuits |
| **CSWAP (Fredkin)** | 3 | Swaps two targets if control is \|1> | Swap test (core operation) |

The Hadamard is key: both outputs have 50/50 measurement probability, but the **sign** of the |1> amplitude differs. That sign has no effect alone, but when combined with other gates, it creates the interference that makes the swap test work.

### 4.5 Entanglement

When qubits interact through gates (like CNOT), their states become **entangled**:

```
(1/sqrt(2))(|00> + |11>)
```

This state can't be described as two separate qubits. Measuring one immediately determines the other. Entanglement creates correlations that quantum algorithms exploit.

> **Analogy:** Like a pair of magic dice -- if you roll one and get 6, the other is guaranteed to be 6, no matter how far apart they are. Not because they communicated, but because they were entangled from the start.

### 4.6 Measurement

Measuring a qubit forces it into a definite state. The outcome is random, governed by |amplitude|^2.

Two consequences:
1. You **cannot** read all 2^n amplitudes from an n-qubit register. One measurement gives one result
2. Algorithms must make the correct answer have **high amplitude** before measuring

### 4.7 Circuits, Depth, and NISQ

- A **quantum circuit** = sequence of gates followed by measurement
- **Circuit depth** = number of sequential gate layers (parallel gates count as one layer)
- On real hardware, qubits lose coherence over time (**decoherence**). Deeper circuits accumulate more error

**NISQ** (Noisy Intermediate-Scale Quantum) = current hardware era. Reliable circuit depth: ~100 layers. Beyond that, noise dominates.

This project tracks circuit depth as a key metric because it directly predicts hardware feasibility. Stored in `circuit_depth` column of `benchmark_results`.

**In one sentence:** Qubits can be in superposition, gates manipulate that superposition, measurement collapses it to a definite answer, and circuit depth determines whether real hardware can run it.

<details>
<summary>Self-test</summary>

**Q: Why can't you just read all 2^n amplitudes out of a quantum register?**
A: Measurement collapses the superposition. You get one random result per measurement. To learn about the amplitudes, you need many measurements (shots).

**Q: What limits the usefulness of current quantum hardware?**
A: Circuit depth. Current NISQ devices reliably run ~100 gate layers. Deeper circuits produce too many errors from decoherence.
</details>

---

## Part 5 -- Grover's Algorithm

### 5.1 The Promise

Unsorted database of N items. Find the one that matches a condition.
- **Classical:** O(N) -- check every item
- **Grover's (1996):** O(sqrt(N)) -- provably optimal

For 1,000,000 items: classical needs ~1M checks, Grover's needs ~1,000.

### 5.2 How It Works

1. **Initialise:** Hadamard on all qubits -> uniform superposition (every item has amplitude 1/sqrt(N))
2. **Repeat ~(pi/4)*sqrt(N) times:**
   - **(a) Oracle:** Flips the sign of the target item's amplitude (marks it without revealing it)
   - **(b) Diffusion:** Reflects all amplitudes around the mean. The target (negative, far below mean) bounces far above. Others barely change
3. **Measure:** Target now has amplitude ~1, so measurement returns it with near-certainty

> **Analogy:** Imagine a trampoline where everyone is standing at the same height. The oracle pushes the target person below the trampoline surface. The diffusion step then flips the whole trampoline upside down -- the person who was below is now the highest. Repeat until they're standing way above everyone else.

### 5.3 Why Exactly (pi/4) * sqrt(N) Iterations

The target's amplitude follows a sine curve. It peaks at (pi/4)*sqrt(N) iterations. Too few: hasn't peaked. Too many: overshoots and drops back down.

### 5.4 Why This Doesn't Directly Help Our Project

Grover's needs all N vectors loaded into superposition simultaneously. This requires **qRAM** -- a theoretical device that loads N vectors in O(log N) steps.

**qRAM does not exist.** Without it, loading each vector costs O(n) gates (n = dimension). Loading all N vectors costs O(N * n) -- **worse than classical brute force**.

This is exactly what our project does: `QiskitSwapTestEngine` runs one circuit per database vector, N times total. O(N) overall. The quantum part is only the similarity computation, not the search.

**This is one of the project's most important findings:** the theoretical O(sqrt(N)) speedup is blocked by state preparation cost.

**In one sentence:** Grover's algorithm could search a database in sqrt(N) time, but it needs qRAM (which doesn't exist) to load the data, so our project runs classical-speed O(N) search with quantum similarity computation.

<details>
<summary>Self-test</summary>

**Q: What is the key prerequisite that Grover's algorithm needs but we don't have?**
A: qRAM -- quantum random access memory that can load all N database vectors into superposition in O(log N) time.

**Q: Since we can't use Grover's, what does the quantum engine actually do?**
A: It runs one swap test circuit per database image, comparing each image vector to the query vector individually. The quantum part is the similarity computation, not the search.
</details>

---

## Part 6 -- Amplitude Encoding and the Swap Test

This is the core quantum technique used in the project.

### 6.1 Amplitude Encoding

To compute similarity on a quantum circuit, vectors must be converted into quantum states. **Amplitude encoding** maps vector components to qubit amplitudes.

For a unit vector v = (v1, v2, ..., vn) where n is a power of 2:

```
|psi_v> = v1|00...0> + v2|00...1> + ... + vn|11...1>
```

Each component becomes the amplitude of one basis state. Since v is a unit vector, the amplitudes satisfy the quantum normalisation requirement automatically.

**Exponential compression:**

| Vector dim | Qubits needed |
|---|---|
| 64 | 6 (because 2^6 = 64) |
| 128 | 7 |
| 512 | 9 |

> **Analogy:** It's like storing a 64-page book in a 6-digit code. Incredibly compact. But writing that code (state preparation) takes as long as reading the whole book -- O(n) gates.

**The caveat:** Preparing an arbitrary amplitude-encoded state requires O(n) gates. This is the bottleneck that cancels Grover's speedup.

**In the code:** `QiskitSwapTestEngine._encode()` normalises and pads the vector to a power of 2, then `circuit.initialize()` in `_run_swap_test()` handles the actual state preparation.

### 6.2 The Swap Test

The swap test estimates |<psi|phi>|^2 -- the squared inner product (= squared cosine similarity on unit vectors).

**The circuit:**

```
ancilla: |0> --H--*--H--M
                  |
state psi: |psi> --X--        (CSWAP targets)
state phi: |phi> --X--
```

**Steps:**
1. Load |psi> (query) and |phi> (database vector) via amplitude encoding
2. Hadamard on ancilla -> puts it in superposition
3. CSWAP: if ancilla is |1>, swap the psi and phi registers
4. Hadamard on ancilla again
5. Measure the ancilla

**The result:**

```
P(0) = (1 + |<psi|phi>|^2) / 2
similarity = sqrt(max(0, 2 * P(0) - 1))
```

**In the code:** `QiskitSwapTestEngine._run_swap_test()` in `backend/src/engines/qiskit_swaptest.py`, lines 84-107.

**Why squared?** The swap test gives |<psi|phi>|^2, not the signed similarity. It can't distinguish +0.8 from -0.8. For CLIP embeddings (which cluster on the positive side), this doesn't matter.

### 6.3 Shot Noise

A circuit doesn't give a deterministic answer. Each execution (**shot**) returns one bit: 0 or 1. To estimate P(0):

```
P(0) ~ (count of 0s) / N_shots
standard error ~ 1 / sqrt(N_shots)
```

| Shots | Standard error in P(0) |
|---|---|
| 512 | ~0.044 |
| 1024 | ~0.031 |
| 2048 | ~0.022 |
| 4096 | ~0.016 |

More shots -> less noise -> better ranking accuracy -> but more expensive on real hardware.

The `quantum_mock_sampler` simulates this noise without circuits: it computes exact cosine similarity, then adds Gaussian noise scaled by `layers / max(1, shots)` (see `QuantumMockEngine.search()` in `backend/src/engines/quantum_mock.py`).

**In one sentence:** Each shot gives one bit of information about the similarity; more shots average out the randomness to reveal the true value.

<details>
<summary>Self-test</summary>

**Q: How does the swap test circuit actually measure similarity?**
A: It creates quantum interference between the two encoded vectors. When they're similar, the interference is constructive (ancilla likely measures 0). When different, it's destructive (ancilla is roughly 50/50).

**Q: Why does the mock engine add noise proportional to layers/shots?**
A: More layers = deeper circuit = more noise. More shots = better averaging = less noise. The ratio captures this trade-off without actually running quantum circuits.
</details>

---

## Part 7 -- The qRAM Problem

### 7.1 What qRAM Would Do

**qRAM** (quantum random access memory) would take a superposition of indices and return a superposition of data:

```
Sum_i alpha_i|i>|0> -> Sum_i alpha_i|i>|v_i>
```

This would load the entire database into superposition in O(log N) steps. With qRAM + Grover's, you could find the most similar vector in O(sqrt(N)).

Without qRAM: encoding each vector costs O(n) gates, all N vectors costs O(N * n) -- worse than classical.

> **Analogy:** Imagine a library where you have to manually copy out each book to check if it matches your query (that's what we do now -- O(N)). qRAM would be like a magic librarian who can instantly check all books simultaneously.

### 7.2 Why This Is the Key Finding

The theoretical speedup is blocked by state preparation cost. The algorithm itself works correctly (our project proves this). The missing piece is efficient data loading.

The project measures per-circuit resource cost (depth, qubits, shots), establishing exactly what would be needed when qRAM becomes available.

### 7.3 Quantum Error Correction (Brief)

Real hardware introduces errors: decoherence, gate errors (~0.1-1% per gate), readout errors. **Quantum error correction** encodes one "logical qubit" using many physical qubits (50-1000 per logical qubit). Current NISQ devices can't afford this overhead.

### 7.4 Current Hardware

- IBM's largest chips: 1000+ physical qubits, reliable depth ~100
- Coherence times: hundreds of microseconds
- Our circuits (13-15 qubits) are well within qubit limits

The project runs on **AerSimulator** -- Qiskit's classical simulator. Mathematically exact (no hardware noise), but exponentially expensive in classical memory: n qubits needs 2^n complex numbers. For 15 qubits: 32,768 numbers (fine). For 40 qubits: impossible.

**In one sentence:** qRAM would unlock the quantum speedup, but it doesn't exist yet; the project measures everything else so the baseline is ready when it does.

<details>
<summary>Self-test</summary>

**Q: What is the fundamental bottleneck preventing quantum speedup in this project?**
A: State preparation (loading vectors into the quantum circuit) costs O(n) gates -- the same as classical search. qRAM would reduce this to O(log N).

**Q: Why are AerSimulator results meaningful even though it's not real quantum hardware?**
A: It's mathematically exact -- same measurement statistics as a perfect noiseless quantum chip. The only noise is shot noise, which is real (also present on actual hardware). Results represent the best-case accuracy ceiling.
</details>

---

## Part 8 -- The Project's Engines and Metrics

### 8.1 The Four Engines

All four implement `SearchEngineStrategy` (defined in `backend/src/engines/base.py`): `build_index()` + `search()`.

| Engine | File | What it does |
|---|---|---|
| **BruteForceCosineEngine** | `brute_force_cosine.py` | NumPy dot products, sorts by score. O(N*d). Exact. **Ground truth baseline.** |
| **FaissFlatEngine** | `faiss_flat.py` | FAISS SIMD-optimised L2 search. Still exact. Faster on large datasets |
| **QuantumMockEngine** | `quantum_mock.py` | Exact cosine + Gaussian noise (stdev = layers/max(1, shots)). No circuits. Fast noise study |
| **QiskitSwapTestEngine** | `qiskit_swaptest.py` | Real swap test circuits on AerSimulator. N circuits per query. **Actual quantum computation** |

All files are in `backend/src/engines/`.

> **Analogy:** Four chefs cooking the same dish. Two use standard recipes (classical). One pretends to use a quantum oven but actually uses a regular one with some random salt (mock). One actually uses the quantum oven (Qiskit). We taste-test all four to see if the quantum oven works.

### 8.2 MRR -- The Quality Metric

**Mean Reciprocal Rank:** Each query has one correct image. The engine ranks all images by similarity.

```
MRR = average of (1 / rank of correct image) across all queries
```

| Rank of correct image | Score for that query |
|---|---|
| 1st | 1.0 |
| 2nd | 0.5 |
| 5th | 0.2 |
| 10th | 0.1 |

MRR directly measures how far a user scrolls before finding the right answer.

**Key implementation detail:** The harness ranks ALL images (no top-K cutoff in `run_benchmarks.py` -- it passes `top_k=len(dataset_ids)`), so the true rank is always captured. Each query maps to one correct image via `BenchmarkQuery.target_id` (strips `query_` prefix).

### 8.3 Quantum-Specific Metrics

| Metric | What it measures | Why it matters | Stored in |
|---|---|---|---|
| **Circuit depth** | Sequential gate layers | Proxy for decoherence risk | `benchmark_results.circuit_depth` |
| **Qubit count** | Qubits for one swap test | Hardware allocation needs | `benchmark_results.num_qubits` |
| **Shots vs. MRR** | Quality at different measurement budgets | Cost parameter on real hardware | Varies `shots` column |

Together: MRR answers "does it work?", depth/qubits answer "what hardware?", shots vs. MRR answers "how many measurements?"

### 8.4 Why Speed Is Not Compared Across Engines

The quantum engine runs on a classical simulator. Its wall-clock time reflects simulating 2^n amplitudes on a CPU -- not what a real quantum chip would take.

**What IS valid:**
- MRR across engines (accuracy doesn't depend on simulator overhead)
- Speed within one engine across dimensions (same computation, different scale)

**In one sentence:** Four interchangeable engines let us compare quantum accuracy against classical ground truth, while tracking qubit count, circuit depth, and shot budget as quantum-specific cost metrics.

<details>
<summary>Self-test</summary>

**Q: Why is `brute_force_cosine` the ground truth, not `faiss_flat_l2`?**
A: Both are exact and give the same ranking. `brute_force_cosine` is used as the named baseline because it's the simplest, most transparent implementation.

**Q: Why can't we compare wall-clock speed between the Qiskit engine and classical engines?**
A: Because the Qiskit engine runs on a classical simulator, so its timing reflects simulation overhead, not actual quantum hardware speed.
</details>

---

## Part 9 -- The Thesis Argument

The full argument, end to end:

1. **Grover's algorithm** gives O(sqrt(N)) quantum search vs O(N) classical -- a proven quadratic speedup

2. Applying it to vector search requires loading vectors via **amplitude encoding**

3. Amplitude encoding costs **O(n) gates per vector** -- same as classical brute force. Speedup cancelled

4. **qRAM** could fix this (load all N vectors in O(log N)). qRAM doesn't exist as practical hardware

5. The **swap test** accurately estimates cosine similarity on AerSimulator, matching classical MRR with enough shots

6. **Circuit depth and qubit count** are measured from actual compiled Qiskit circuits, giving concrete hardware requirements

7. **Conclusion:** The quantum approach is algorithmically correct but blocked by state preparation cost. The project provides the accuracy baseline, resource cost model, and benchmarking framework needed to re-evaluate when hardware improves

**What we are NOT claiming:** That quantum is faster, or that it will be. We are establishing that the algorithm works, measuring what it costs, and identifying what needs to change (qRAM) before it becomes competitive.

> **How to frame this at a defense:** "We proved the algorithm works under ideal conditions, measured what it would cost on real hardware, and identified the specific missing technology (qRAM) that prevents it from being practical. This positions our framework as a ready-made baseline for when quantum hardware catches up."

<details>
<summary>Self-test</summary>

**Q: Summarise the thesis in one sentence.**
A: The quantum swap test correctly performs cross-modal vector search on a simulator, but state preparation cost (O(n) per vector) prevents it from being faster than classical search until qRAM becomes available.

**Q: What are the three things this project contributes?**
A: (1) Empirical proof the swap test works on AerSimulator, (2) measured circuit depth and qubit counts at each dimension, (3) a benchmarking framework ready for re-evaluation on future hardware.

**Q: What is the most common misconception an examiner might have about this project?**
A: That it claims quantum is faster. It does not. It measures whether the quantum algorithm is correct and what hardware resources it needs.
</details>
