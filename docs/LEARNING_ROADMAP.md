# Learning Roadmap

Everything you need to understand this project, from basic math to quantum circuits to the thesis argument. Read straight through - each part builds on the last.

**Who this is for:** You can write code but have never studied quantum physics.

---

## Part 1 - Vectors and Similarity

### Vectors

A **vector** is just a list of numbers: `v = (v1, v2, ..., vn)`. In this project, vectors represent *meaning*. CLIP converts a sentence into 512 numbers and an image into another 512 numbers. If the sentence describes the image, their vectors end up close together.

> Like GPS coordinates, but with 512 dimensions instead of 2. Similar things have nearby coordinates.

### Dot product

Multiply matching components and add them up: `a . b = a1*b1 + a2*b2 + ... + an*bn`

- Large positive = similar
- Near zero = unrelated
- Negative = opposite

### Normalisation

- **L2 norm** = length of the vector: `||v|| = sqrt(v1^2 + ... + vn^2)`
- **Normalising** divides by length, producing a **unit vector** (length = 1)
- This project normalises everything first (`CLIPEmbeddingModel.encode_texts()` and `encode_images()` both use `torch.nn.functional.normalize`)
- After normalising, **cosine similarity = dot product = equivalent L2 ranking**. All three metrics agree on which vectors are closest

### Cosine similarity

`cos(theta) = (a . b) / (||a|| * ||b||)` - ranges from -1 (opposite) to +1 (identical).

On unit vectors this is just the dot product. The swap test computes |a . b|^2 (same thing, squared). The squaring can't tell +0.8 from -0.8, but CLIP vectors cluster on the positive side so this doesn't matter.

**In one sentence:** Normalise vectors, then a dot product tells you how similar two things are.

**Self-test**

**Q: Why normalise before comparing?**
A: So cosine, dot product, and L2 all give the same ranking - and so vectors satisfy the quantum requirement that amplitudes squared sum to 1.

**Q: Cosine similarity of a unit vector with itself?**
A: 1.0.


---

## Part 2 - Classical Search

### The problem

Given a query vector q and N database vectors, find the most similar ones. This is **k-nearest-neighbour (kNN)** search.

### Brute force

Compare q against every single vector. N dot products, sort, return the top K.
- **Cost:** O(N) per query
- **Accuracy:** Perfect - always finds the true nearest neighbours
- **In the code:** `BruteForceCosineEngine` in `backend/src/engines/brute_force_cosine.py` - does `self._matrix @ query` (one giant matrix multiply)

> Like finding the tallest person by measuring everyone. Guaranteed correct, but slow in a crowd.

### FAISS

Same brute-force logic but using Facebook's FAISS library (hardware-optimised). Still exact, just faster in practice. Uses L2 distance, which gives the same ranking on normalised vectors.
- **In the code:** `FaissFlatEngine` in `backend/src/engines/faiss_flat.py`, wraps `faiss.IndexFlatL2`

### HNSW (approximate)

For millions of vectors, brute force is too slow. **HNSW** (Hierarchical Navigable Small World) builds a multi-layer graph for O(log N) lookup. Trade-off: might miss the exact nearest neighbour.
- **In the code:** `FaissHnswEngine` in `backend/src/engines/faiss_hnsw.py`, wraps `faiss.IndexHNSWFlat`
- pgvector uses HNSW for `image_vectors` (see `db/migrations/up/1_initial_schema.sql`). For ~20 images brute force is fine; HNSW matters at thousands+

> Like looking up a word in a dictionary - you jump to roughly the right section, then narrow down.

**In one sentence:** Classical search either checks every vector (brute force, O(N)) or uses an index (HNSW, O(log N)) to skip most of them.

**Self-test**

**Q: Why include both `brute_force_cosine` and `faiss_flat_l2`?**
A: Brute-force is a transparent baseline. FAISS demonstrates a production-grade implementation. Both are exact.

**Q: Why include HNSW as a benchmark engine?**
A: HNSW (O(log N) approximate) is the most relevant classical comparison for the quantum question - it beats Grover even with ideal qRAM for practical approximate search. It completes the picture: brute force (O(N) exact), FAISS flat (O(N) exact, optimised), HNSW (O(log N) approximate), and quantum.


---

## Part 3 - CLIP and Embeddings

### What is an embedding?

A function that converts input (text, image, audio) into a fixed-length vector, trained so that similar inputs get similar vectors.

> A sommelier assigning flavour scores to every wine. Similar wines get similar scores. The scores ARE the embedding.

### CLIP

**CLIP** (Contrastive Language-Image Pre-training, OpenAI 2021) has two encoders:
- **Image encoder** (ViT-B/32): image -> 512-dim vector
- **Text encoder** (Transformer): text -> 512-dim vector

The key insight: **both output into the same vector space**. A photo of a dog and the sentence "a dog on a beach" end up near each other. This is what makes text-to-image search possible.

**In the code:** `CLIPEmbeddingModel` in `backend/src/pipeline/clip_model.py`. Auto-detects CUDA / MPS / CPU - runs on CPU without a GPU.

### Truncation

CLIP outputs 512 dims. The project **truncates** to smaller sizes (64, 128) to study how dimension affects accuracy vs. quantum cost. Configured in `benchmarks.yaml` under `dimensions:`, applied by `_prepare_vectors()` in `run_benchmarks.py`.

**In one sentence:** CLIP puts text and images into the same 512-number vector space; we normalise and optionally truncate before feeding to any engine.

**Self-test**

**Q: Why can we search for images using text?**
A: CLIP maps both into the same vector space. Similar meanings = nearby vectors, regardless of input type.

**Q: What does truncation from 512 to 64 dimensions cost?**
A: Some accuracy loss (fewer features captured), but fewer qubits needed (6 per register instead of 9).


---

## Part 4 - Quantum Computing Essentials

### Qubits

A classical bit is 0 or 1. A **qubit** can be in **superposition**: both 0 and 1 at the same time, described by two numbers (amplitudes):

`|psi> = alpha|0> + beta|1>`, where |alpha|^2 + |beta|^2 = 1

- **Measuring** gives 0 with probability |alpha|^2, or 1 with probability |beta|^2
- Before measurement, amplitudes can **interfere** - this is what makes quantum algorithms work

> A classical bit is a light switch (on or off). A qubit is a dial on a sphere. When you look (measure), it snaps to on or off based on where the dial was pointing.

### Multiple qubits and quantum parallelism

n qubits represent 2^n states simultaneously. One operation affects all states at once.

| Qubits | States in superposition |
|---|---|
| 10 | 1,024 |
| 20 | ~1 million |
| 50 | ~10^15 |

The catch: you can't read all 2^n answers. Measurement collapses to **one** random result. Algorithms must make the right answer likely before measuring.

### Interference

When different paths through a circuit lead to the same state, their amplitudes add:
- Same sign = **constructive** (probability increases)
- Opposite signs = **destructive** (probability decreases)

Every quantum algorithm engineers the circuit so wrong answers cancel and the right answer amplifies.

### Gates

Gates are reversible operations on qubits:

| Gate | Qubits | What it does | Used in |
|---|---|---|---|
| **Hadamard (H)** | 1 | Creates equal superposition | Swap test ancilla, Grover init |
| **CNOT** | 2 | Flips target if control is 1 | General circuits |
| **CSWAP (Fredkin)** | 3 | Swaps two targets if control is 1 | Swap test core |
| **MCX** | n | Multi-controlled NOT | Grover oracle |

### Circuit depth and NISQ

- **Circuit depth** = number of sequential gate layers
- Real qubits lose coherence over time (**decoherence**) - deeper circuits = more error
- **NISQ** (Noisy Intermediate-Scale Quantum) = current hardware era. Reliable depth: ~100 layers

This project tracks circuit depth in `benchmark_results.circuit_depth` because it directly predicts whether real hardware can run the circuit.

**In one sentence:** Qubits hold superpositions, gates manipulate them, measurement collapses to one answer, and circuit depth determines if real hardware can run it.

**Self-test**

**Q: Why can't you read all 2^n amplitudes?**
A: Measurement collapses to one random result. You need many shots (repeated measurements) to estimate probabilities.

**Q: What limits current quantum hardware?**
A: Circuit depth. NISQ devices handle ~100 gate layers before noise dominates.


---

## Part 5 - Amplitude Encoding and the Swap Test

This is the core quantum technique in the project.

### Amplitude encoding

To use a quantum circuit, vectors must become quantum states. **Amplitude encoding** maps each vector component to a qubit amplitude:

`|psi_v> = v1|00...0> + v2|00...1> + ... + vn|11...1>`

- **Compression:** 64 dims = 6 qubits (2^6 = 64)
- **Cost:** Preparing an arbitrary state takes O(n) gates - this is the bottleneck that cancels Grover's speedup (see Part 6)

> Storing a 64-page book in a 6-digit code. Incredibly compact, but writing the code takes as long as reading the book.

**In the code:** `QiskitSwapTestEngine._encode()` normalises and pads to power of 2, then `circuit.initialize()` in `_run_swap_test()` does state preparation.

### The swap test circuit

Estimates |<psi|phi>|^2 - the squared cosine similarity of two unit vectors.

**How it works:**
1. Encode query vector and database vector into two quantum registers (amplitude encoding)
2. Apply Hadamard to an ancilla qubit (puts it in superposition)
3. Apply CSWAP: if ancilla is |1>, swap the two registers
4. Apply Hadamard to ancilla again
5. Measure the ancilla: **P(0) = (1 + |<psi|phi>|^2) / 2**
6. Solve for similarity: `similarity = sqrt(max(0, 2*P(0) - 1))`

**In the code:** `QiskitSwapTestEngine._run_swap_test()` in `backend/src/engines/qiskit_swaptest.py`

| Vector dim | Qubits per register | Total qubits (2 registers + 1 ancilla) |
|---|---|---|
| 64 | 6 | **13** |
| 128 | 7 | **15** |
| 512 | 9 | **19** |

### Shot noise

Each circuit run returns one bit (0 or 1). To estimate P(0), you run many **shots** and average:

| Shots | Standard error in P(0) |
|---|---|
| 512 | ~0.044 |
| 2048 | ~0.022 |
| 4096 | ~0.016 |

For reference, standard error in P(0) = 1/sqrt(shots). At 512 shots that's ~0.044; at 2048 it drops to ~0.022.

**In one sentence:** The swap test uses quantum interference to measure vector similarity; more shots = more accurate estimate.

**Self-test**

**Q: If two vectors are identical (similarity = 1.0), what's P(0)?**
A: (1 + 1) / 2 = 1.0. The ancilla always measures 0.

**Q: If two vectors are orthogonal (similarity = 0)?**
A: (1 + 0) / 2 = 0.5. The ancilla is a fair coin - maximum uncertainty.


---

## Part 6 - Grover's Algorithm

### The promise

Find one matching item in an unsorted database of N items:
- **Classical:** O(N) - check every item
- **Grover's (1996):** O(sqrt(N)) - provably optimal

For 1,000,000 items: classical ~1,000,000 checks, Grover's ~785.

### How it works

1. **Initialise:** Hadamard on all index qubits -> uniform superposition over all N items
2. **Repeat floor(pi*sqrt(N)/4) times:**
   - **Oracle:** Flips the phase of the target item's amplitude (marks it)
   - **Diffusion:** Reflects all amplitudes around the mean - the marked item bounces above everyone else
3. **Measure:** Target now has probability ~1

> Everyone standing at the same height on a trampoline. The oracle pushes the target below the surface. Diffusion flips the trampoline - the pushed person is now highest. Repeat until they tower over everyone.

**In the code:** `QiskitGroverEngine` in `backend/src/engines/qiskit_grover.py`. The oracle is `_apply_oracle()` (phase flip via X gates + MCX). The diffusion operator is `_apply_diffusion()` (H, X, MCX, X, H).

### Why it doesn't give us a speedup today

Grover's needs all N vectors in superposition *simultaneously*. This requires **qRAM** - theoretical hardware that loads N vectors in O(log N) steps. **qRAM does not exist.**

Without qRAM, loading each vector costs O(n) gates. Loading all N = O(N) - the same cost as classical search. The O(sqrt(N)) search savings are wiped out by the O(N) loading cost.

**What the Grover engine actually does:** Pre-computes the closest match classically (the O(N) step that qRAM would replace), then runs the Grover circuit to find it in O(sqrt(N)) iterations. This isolates the search step so we can measure oracle call counts and verify O(sqrt(N)) scaling.

**In one sentence:** Grover's could search in sqrt(N) time, but needs qRAM to load data - so we benchmark the search step alone and document the qRAM bottleneck.

**Self-test**

**Q: For N = 1,000,000, how many Grover iterations are needed?**
A: floor(pi * sqrt(1,000,000) / 4) = floor(pi * 1000 / 4) ~ 785.

**Q: Why does the Grover engine pre-compute the answer classically?**
A: To build the oracle (which marks the correct item). Without qRAM, there's no way to avoid this O(N) classical step. The value is in measuring the O(sqrt(N)) search, not the loading.


---

## Part 7 - The qRAM Problem

### What qRAM would do

**qRAM** would take a superposition of indices and return a superposition of the corresponding data - loading the entire database in O(log N) steps. Combined with Grover's: O(sqrt(N)) total search.

Without it: encoding each vector = O(n) gates. All N vectors = O(N) total. No speedup.

> A library where you must manually photocopy each book to check it (O(N)). qRAM = a magic librarian who can check all books simultaneously in O(log N) time.

### Current hardware reality

- IBM's largest chip: ~1,100 qubits, reliable depth ~100
- qRAM is a completely different hardware architecture (quantum memory array with tree routing), not just "more qubits"
- Fault-tolerant computing needs ~1,000 physical qubits per logical qubit
- For 1,000,000 vectors: ~1 billion physical qubits for qRAM alone

### The project's approach

The algorithm works (we prove it). The bottleneck is data loading. We measure per-circuit resource cost (depth, qubits, shots) to establish exactly what's needed when qRAM arrives.

We use **AerSimulator** (Qiskit's noiseless simulator) - mathematically exact, same statistics as a perfect quantum chip. The only noise is shot noise (from finite measurements), which also exists on real hardware. Results are the best-case accuracy ceiling.

**In one sentence:** qRAM would unlock quantum speedup but doesn't exist; we measure everything else so the baseline is ready.

**Self-test**

**Q: Why can't IBM's 1,100 qubits be used as qRAM?**
A: Those are processor qubits for gate circuits. qRAM needs a completely different architecture (quantum memory with tree routing). Like having transistors but needing capacitors.

**Q: Why are simulator results meaningful?**
A: Mathematically exact - same statistics as a perfect chip. Shot noise is real. Results are the best-case ceiling.


---

## Part 8 - Engines and Metrics

### The engines

All implement `SearchEngineStrategy` (`build_index()` + `search()`) in `backend/src/engines/base.py`:

| Engine | File | What it does | O(?) |
|---|---|---|---|
| `brute_force_cosine` | `brute_force_cosine.py` | NumPy dot products. Exact. **Ground truth** | O(N) |
| `faiss_flat_l2` | `faiss_flat.py` | FAISS L2 search. Exact. Production-grade | O(N) |
| `faiss_hnsw_l2` | `faiss_hnsw.py` | FAISS HNSW graph search. Approximate classical baseline | O(log N) |
| `hybrid_hnsw_swap_test` | `hybrid_hnsw_swaptest.py` | HNSW prefilter plus swap-test reranking | O(log N + M) |
| `qiskit_swap_test` | `qiskit_swaptest.py` | Real swap test on AerSimulator | O(N) |
| `qiskit_grover` | `qiskit_grover.py` | Grover's algorithm on AerSimulator | O(sqrt(N)) oracle calls |

> Multiple engines cooking the same dish. Classical engines retrieve candidates, quantum engines estimate similarity or amplify a marked state, and the hybrid engine combines both ideas.

### MRR (Mean Reciprocal Rank)

The main quality metric. Each query has one correct image. The engine ranks all images.

`MRR = average of (1 / rank of correct image) across all queries`

| Correct at rank... | MRR score |
|---|---|
| 1st | 1.0 |
| 2nd | 0.5 |
| 5th | 0.2 |

The harness computes MRR over the top_k results (`top_k=selection.top_k`, default 10, in `run_benchmarks.py`). If the correct image isn't in the top 10, MRR = 0 for that query. Each query maps to one correct image via `BenchmarkQuery.target_id`.

### Operation count - the cross-engine scaling KPI

- Exact classical engines: N comparisons per query
- HNSW: approximate O(log N) graph traversal
- Hybrid HNSW + swap test: O(log N + M), where M is the candidate pool reranked quantumly
- Grover: floor(pi*sqrt(N)/4) oracle calls per query
- Stored in `benchmark_results.oracle_calls`
- This is the **only valid cross-engine speed comparison** (hardware-independent)

### Why wall-clock speed is NOT compared across engines

The quantum engines run on a classical simulator. Their timing reflects simulating 2^n amplitudes on a CPU, not real quantum hardware speed. MRR is valid across engines. Speed is only valid *within* one engine across dimensions.

**In one sentence:** Interchangeable engines let us compare classical, quantum, and hybrid accuracy, with oracle count as the scaling KPI and MRR as the quality KPI.

**Self-test**

**Q: Why is brute-force cosine the ground truth?**
A: Simplest, most transparent exact implementation.

**Q: Why can't we compare wall-clock speed across engines?**
A: Quantum engine timing reflects CPU simulation overhead, not real quantum hardware speed.


---

## Part 9 - The Thesis Argument

The full argument, end to end:

1. **Grover's algorithm** gives O(sqrt(N)) quantum search - a proven quadratic speedup
2. Applying it to vector search requires **amplitude encoding**, which costs **O(n) gates per vector** - same as classical. Speedup cancelled without qRAM
3. **qRAM** could fix this (load all vectors in O(log N)). qRAM doesn't exist
4. The **swap test** accurately estimates cosine similarity on AerSimulator, matching classical MRR with enough shots
5. The **Grover engine** demonstrates O(sqrt(N)) oracle scaling on the search step, verified empirically
6. **Circuit depth and qubit count** are measured from actual compiled Qiskit circuits, giving concrete hardware requirements
7. **Conclusion:** The quantum approach is correct but blocked by state preparation cost. The project provides the accuracy baseline, resource model, and framework ready for re-evaluation when hardware improves

**What we are NOT claiming:** That quantum is faster, or that it will be. We prove the algorithms work, measure what they cost, and identify the specific missing hardware (qRAM).

> **How to frame at a defence:** "We proved the algorithms work under ideal conditions, measured their cost, and identified the missing technology (qRAM) that prevents practical speedup. Our Grover oracle scales as O(sqrt(N)) on the simulator. The system is architecturally ready for when quantum hardware catches up."

**Self-test**

**Q: Summarise the thesis in one sentence.**
A: Quantum swap test and Grover's algorithm correctly perform vector search on a simulator, but state preparation cost prevents end-to-end speedup until qRAM becomes available.

**Q: Three contributions of this project?**
A: (1) Empirical proof both swap test and Grover work, (2) measured circuit depth, qubit counts, and oracle scaling, (3) a complete benchmarking framework ready for future hardware.

**Q: Most common examiner misconception?**
A: That the project claims quantum is faster. It doesn't - it measures correctness and cost.


---
*Last updated: 2026-05-20.*
