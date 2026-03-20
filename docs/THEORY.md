# Theory Guide: Quantum-Enhanced Multi-Modal Vector Search

## 1. The Problem: Cross-Modal Similarity Search

**Cross-modal search** means searching one type of data (e.g., text) and getting results in a
different type (e.g., images). Classic keyword search cannot do this — a search for "a dog
running on a beach" cannot match an image that has no text label.

The solution is to map both text and images into a **shared vector space** where meaning
determines proximity: the vector for the text "dog on a beach" should sit close to the vector
for an actual photo of a dog on a beach, even though they are completely different data types.

This project builds and benchmarks exactly that:
- A shared embedding pipeline (CLIP) converts both text and images into vectors.
- Multiple search engines find the nearest vectors to a text query.
- The result set contains images that are semantically close to the query.

---

## 2. Embeddings and Vector Spaces

An **embedding** is a fixed-length array of floating-point numbers (a vector) that represents
an object's meaning. Two objects with similar meanings have vectors that are close in space.

### Why vectors?

Mathematical operations on vectors are cheap and well-understood:
- Distance tells us how similar two things are.
- The same operations work regardless of whether the original data is text, an image, audio, etc.

### Dimensionality

The length of the vector is its **dimension**. CLIP's ViT-B/32 produces 512-dimensional vectors.
For benchmarking, the project truncates these to 64 or 128 dimensions to study how dimensionality
affects accuracy and quantum resource cost.

**Truncation** works because the most informative components tend to cluster near the front of
CLIP embeddings (a property of the training objective), so cutting from the tail loses less
information than cutting from the middle.

### The embedding space mental model

Imagine a 512-dimensional room where every image and every piece of text has an assigned seat.
CLIP has been trained so that a sentence and its matching image sit next to each other, while
unrelated content sits far away. A nearest-neighbour query is just: "give me the K closest seats
to this query."

---

## 3. CLIP: The Embedding Model

**CLIP** (Contrastive Language-Image Pre-training) was published by OpenAI in 2021.

### Architecture

CLIP has two independent encoders trained jointly:
- **Image encoder** — a Vision Transformer (ViT). ViT-B/32 means "Base" size, patch size 32×32.
  An input image is split into 32×32 pixel patches. Each patch is linearly projected into a token,
  then processed by a standard Transformer architecture.
- **Text encoder** — a smaller Transformer that tokenizes and encodes text.

Both encoders project to the same 512-dimensional space. That is what makes cross-modal search
possible: they share an output space.

### Training: Contrastive Loss

CLIP was trained on ~400 million (image, text caption) pairs scraped from the internet.

For each batch of N pairs, it forms an N×N matrix of (image, text) cosine similarities.
The training objective (InfoNCE / NT-Xent loss) pushes the N correct pairs to have high
similarity, and the N²−N incorrect pairs to have low similarity. This forces the model to learn
general visual and semantic concepts, not just surface-level patterns.

The result: CLIP performs **zero-shot** classification and search — it was never shown your
specific dataset, yet it knows "forest" should sit near photos of trees.

### ViT-B/32 details

| Property | Value |
|---|---|
| Architecture | Vision Transformer |
| Patch size | 32×32 pixels |
| Input resolution | 224×224 |
| Model size | "Base" (~86M parameters in image encoder) |
| Output dimension | 512 |

### L2 Normalisation

After encoding, vectors are optionally L2-normalised (divided by their Euclidean norm so
‖v‖ = 1). On the unit hypersphere:

- Cosine similarity equals the dot product.
- Euclidean distance and cosine distance become interchangeable (L2² = 2 − 2·cos θ).

The project normalises by default in `index_dataset.py` and in the benchmark harness.

---

## 4. Similarity Metrics

### Cosine Similarity

```
cos(θ) = (a · b) / (‖a‖ · ‖b‖)
```

Ranges from −1 (opposite) to 1 (identical). Ignores vector magnitude; only the direction
matters. Ideal for embeddings where magnitude carries no meaning.

### Euclidean (L2) Distance

```
d(a, b) = ‖a − b‖ = sqrt(Σᵢ (aᵢ − bᵢ)²)
```

Smaller means more similar. FAISS `IndexFlatL2` uses this metric. After L2 normalisation,
L2 distance and cosine similarity are monotonically related, so they produce the same ranking.

### Dot Product

When vectors are unit-normalised, the dot product `a · b` equals the cosine similarity.
The quantum swap test measures the squared dot product |⟨ψ|φ⟩|² of the corresponding
quantum states — see Section 8.

### Which metric to use?

For CLIP embeddings, **cosine similarity** (or equivalently, dot product on unit vectors) is
standard. The project uses:
- `BruteForceCosineEngine`: cosine similarity directly.
- `FaissFlatEngine`: L2 distance (equivalent after normalisation).
- `QiskitSwapTestEngine`: squared dot product via swap test.

---

## 5. Classical Search Engines

### 5.1 Brute-Force Cosine (BruteForceCosineEngine)

The simplest possible approach:
1. Normalise every stored vector to unit length.
2. For a query vector q, compute the dot product with every stored vector.
3. Sort descending, return the top K.

Complexity: **O(n · d)** per query (n = dataset size, d = dimension). Exact. No data structure
overhead. Used as a deterministic baseline.

### 5.2 FAISS IndexFlatL2 (FaissFlatEngine)

**FAISS** (Facebook AI Similarity Search) is a library for efficient similarity search on
dense vectors.

`IndexFlatL2` is its simplest index: an exact brute-force scan using L2 distance, but
implemented with highly optimised BLAS/SIMD instructions. It is not approximate — it always
returns the true nearest neighbours. For small datasets (hundreds to thousands of vectors)
it is extremely fast.

The engine stores all vectors as a float32 matrix in memory. On `search()` it calls
`index.search(query, top_k)` which returns distances and positional indices in a single call.
The project code is Python — FAISS is used as a Python library (`import faiss`); the C++ is
an internal implementation detail of the library itself, not something the project code touches.

Why FAISS over pure NumPy? FAISS uses vectorised CPU instructions (AVX2, SSE4) and
multithreading under the hood. For larger datasets it also offers approximate indices (IVF, HNSW).

### 5.3 HNSW (in pgvector — not in the search engines, but in vector storage)

**HNSW** (Hierarchical Navigable Small World) is an approximate nearest-neighbour (ANN)
algorithm used by pgvector for the `image_vectors` table index.

The idea: build a multi-layer graph over the vectors.
- Upper layers have few nodes and long-range "express lane" edges — used for coarse navigation.
- Lower layers have many nodes and short-range edges — used for fine-grained local search.

Search starts at the top layer, greedily moves toward the query, then descends to finer layers.
Query complexity is **O(log n)** on average, compared to O(n) for brute force. The trade-off is
a small chance of missing the exact nearest neighbour (hence "approximate").

Parameters:
- `m` — number of connections per node (higher = more accurate, more memory).
- `ef_construction` — beam width during index build (higher = more accurate, slower build).

---

## 6. Quantum Computing Fundamentals

### 6.1 Classical bits vs qubits

A classical bit is either 0 or 1. A **qubit** is a two-level quantum system that can be in a
**superposition** of both states simultaneously:

```
|ψ⟩ = α|0⟩ + β|1⟩
```

α and β are complex numbers called **amplitudes**. They satisfy |α|² + |β|² = 1.
When you **measure** the qubit, it collapses to |0⟩ with probability |α|² and to |1⟩ with
probability |β|².

Key insight: before measurement, the qubit simultaneously encodes both outcomes. A register of
n qubits encodes 2ⁿ basis states simultaneously.

### 6.2 Quantum gates

Quantum gates are unitary matrices that transform qubit states. Common gates:

| Gate | Notation | Effect |
|---|---|---|
| Hadamard | H | \|0⟩ → (\|0⟩ + \|1⟩)/√2 — creates superposition |
| Pauli-X | X | \|0⟩ ↔ \|1⟩ — classical NOT |
| CNOT | CX | Flips target qubit if control is \|1⟩ |
| Toffoli / CCNOT | CCX | Flips target if both controls are \|1⟩ |
| CSWAP (Fredkin) | — | Swaps two target qubits if control is \|1⟩ |

All gates are **reversible** (unitary), which is a fundamental constraint of quantum mechanics.

### 6.3 Entanglement

When two qubits interact through a gate (e.g., CNOT), their states can become **entangled**:
measuring one instantly determines the other's state, regardless of distance.

Entanglement is essential for quantum algorithms because it creates correlations that no
classical system can efficiently replicate.

### 6.4 Quantum circuits

A quantum circuit is a sequence of gate operations applied to a qubit register, ending in
measurements. The **circuit depth** is the number of layers of gates that cannot be parallelised
(i.e., gates that must run sequentially because they share qubits). Deeper circuits take longer
to execute and accumulate more errors on real hardware.

### 6.5 AerSimulator (used in this project)

This project runs quantum circuits on `AerSimulator`, which is a **classical software simulation**
of a quantum computer provided by Qiskit (IBM). It is exact — there is no hardware noise — but
it uses exponential classical memory to represent quantum states, making large circuits slow.

---

## 7. Amplitude Encoding

To use quantum circuits for vector similarity, we must first encode classical vectors into
quantum states. The standard method is **amplitude encoding**.

For a classical vector **v** = (v₁, v₂, …, v_n) with ‖**v**‖ = 1 and n = 2^k:

```
|ψ⟩ = v₁|0…0⟩ + v₂|0…1⟩ + … + vₙ|1…1⟩ = Σᵢ vᵢ |i⟩
```

The vector's components become the amplitudes of a k-qubit quantum state. This requires only
**log₂(n) qubits** to represent n values — an exponential compression.

### In this project

- The project truncates CLIP vectors to `dim` (64 or 128) dimensions.
- Vectors are padded to the next power of two (64 → 64 = 2^6, 128 = 2^7).
- 64-dim vectors use 6 qubits each; 128-dim use 7 qubits each.
- The swap test needs two such registers + 1 ancilla qubit.
- Total qubits for dim=64: 6 + 6 + 1 = **13 qubits**.
- Total qubits for dim=128: 7 + 7 + 1 = **15 qubits**.

### Caveat

Amplitude encoding is compact in qubits but **expensive to prepare**: encoding an arbitrary
n-dimensional vector generally requires O(n) gates. This is a known bottleneck — the state
preparation cost can cancel out the savings from quantum computation. This is one of the
open research questions in quantum ML.

---

## 8. The Swap Test

The **swap test** is a quantum circuit that estimates the inner product (overlap) of two
quantum states. It is the core of the `QiskitSwapTestEngine`.

### Circuit

```
ancilla:  |0⟩ ──H──●──H──M
                   │
state ψ:  |ψ⟩ ─────X──────   (CSWAP targets)
state φ:  |φ⟩ ─────X──────
```

Steps:
1. Prepare ancilla qubit in |0⟩. Load state |ψ⟩ (query vector) and |φ⟩ (dataset vector).
2. Apply Hadamard to ancilla → ancilla is now (|0⟩ + |1⟩)/√2.
3. Apply a **CSWAP** (Fredkin) gate: if ancilla = |1⟩, swap |ψ⟩ and |φ⟩ registers.
4. Apply Hadamard to ancilla again.
5. Measure the ancilla.

### Mathematics

The probability that the ancilla is measured as |0⟩ is:

```
P(ancilla = 0) = (1 + |⟨ψ|φ⟩|²) / 2
```

Rearranging to get the squared overlap:

```
|⟨ψ|φ⟩|² = 2 · P(0) − 1
```

When states are normalised unit vectors, ⟨ψ|φ⟩ equals the cosine similarity. So:

```
similarity ≈ sqrt(max(0, 2 · P(0) − 1))
```

This is exactly what the code does in `qiskit_swaptest.py`.

### Why squared?

The swap test gives |⟨ψ|φ⟩|², the **squared** dot product, not the signed cosine similarity.
This means it cannot distinguish vectors that are similar from vectors that are opposite in
direction (negative cosine similarity maps to 0). For ranking purposes this is acceptable as
long as the query and corpus vectors are on the same hemisphere — which is generally true for
L2-normalised CLIP embeddings.

### Cost: one circuit per (query, dataset item) pair

For each search query, the engine runs one swap test circuit per dataset vector. For a dataset
of n items and top_k results, this is n circuit executions. On a simulator this is very slow
for large n; on real quantum hardware it would be done in parallel (quantum parallelism),
though the improvement is limited by the state preparation overhead.

---

## 9. Quantum Noise and Shots

### What is shot noise?

A quantum circuit does not produce a deterministic result. Measuring the ancilla qubit once
gives a single bit: 0 or 1. Running the circuit many times and counting how often we see 0
gives an estimate of P(0).

Each circuit execution is called a **shot**. The estimate after N shots has statistical error:

```
standard error ≈ 1 / sqrt(N)
```

With 2048 shots (the project default), the standard error in P(0) is about 0.022. This
propagates through the similarity calculation and causes the quantum engine to rank items
differently from the ground truth on some queries.

### The QuantumMockEngine

The `QuantumMockEngine` does not run real circuits. Instead it:
1. Computes exact cosine similarity (as a stand-in for the true quantum result).
2. Adds Gaussian noise with standard deviation `layers / max(1, shots)`.

This simulates what you would observe if you ran a real shot-based quantum computer: correct
results on average, but with statistical fluctuation. It is faster and useful for studying
the shots-vs-accuracy trade-off without waiting for actual Qiskit simulation.

### Circuit depth and decoherence

On real quantum hardware (not simulators), qubits lose their quantum state over time via
**decoherence** — interaction with the environment causes the quantum information to leak away.
The time a qubit stays coherent is called the **coherence time** (T1 and T2 times, measured in
microseconds on current hardware).

**Circuit depth** — the number of sequential gate layers — determines how long the computation
takes. Deeper circuits run longer and therefore accumulate more decoherence error.

This is why circuit depth is tracked as a KPI: it is a proxy for how feasible the algorithm
would be on actual quantum hardware. Current NISQ (Noisy Intermediate-Scale Quantum) devices
can execute circuits of depth ~100 reliably; deeper circuits produce mostly noise.

---

## 10. Why We Cannot Compare Speeds

**The short answer:** the quantum engine runs on a classical software simulator, so its runtime
reflects classical simulation overhead, not quantum computation time. Comparing wall-clock times
would be meaningless and misleading.

**The long answer:**

Simulating n qubits classically requires 2ⁿ complex numbers (exponential memory). AerSimulator
does this exactly. For 15 qubits, that is 32,768 complex numbers — manageable, but far slower
than hardware quantum execution would be.

On real quantum hardware:
- Gate operations take nanoseconds to microseconds.
- The swap test for a 128-dim vector would take ~tens of microseconds total.
- However, state preparation of amplitude-encoded vectors is O(n) gates, which is the real
  bottleneck, not the swap test itself.

What is meaningful to compare:
- **Accuracy** — does the quantum engine return the same top-K as the classical engines?
- **Circuit depth** — how deep a circuit do we need per query? This predicts real-hardware
  feasibility.
- **Qubit count** — how many qubits? This predicts hardware allocation cost.
- **Shots vs. accuracy** — how many measurements are needed to match classical accuracy?
- **Scaling behaviour** — how do these resource costs grow as dimension increases?

---

## 11. Evaluation Metrics

### 11.1 Weighted Accuracy (NDCG-lite)

Each query in the ground truth has a `target_ids` list — one or more images that are correct
answers for that query. The current dataset has one target per query, but the data model and
all metrics support multiple targets (e.g., a "car" query could legitimately match several car
images). The weighted accuracy scores based on the highest-ranked target found:

| Rank | Weight |
|---|---|
| 1 | 1.00 |
| 2 | 0.66 |
| 3 | 0.33 |
| Not found | 0.00 |

This is a simplified **NDCG** (Normalised Discounted Cumulative Gain), which is the standard
information retrieval metric for ranked result quality. It rewards finding the correct item
higher in the list.

### 11.2 Recall@K

```
Recall@K = (number of relevant items found in top K) / (total relevant items for that query)
```

Answers the question: "out of all images that should match this query, how many did the engine
actually return in its top K results?"

- A query with 3 correct images where the engine finds 2 of them scores 2/3 ≈ 0.67.
- A query with 1 correct image where the engine finds it scores 1/1 = 1.0.
- If none of the correct images appear in the top K, the score is 0.

The final Recall@K is averaged over all queries.

### 11.3 Mean Reciprocal Rank (MRR)

```
MRR = (1/|Q|) · Σ_q  1/rank(q)
```

Where `rank(q)` is the position of the first relevant result for query q (the first hit among
all `target_ids`). If the first match is at rank 1: contributes 1.0. At rank 2: 0.5. At rank 3: 0.33.
Not found: contributes 0.

MRR is particularly useful when you care primarily about the first relevant result.

### 11.4 Why cross-engine speed comparison is excluded

See Section 10. Intra-engine speed comparison (e.g., dim=64 vs dim=128 for the same engine)
is valid because the same type of computation is being compared at different scales.

---

## 12. Vector Storage with pgvector

### Why persistent vector storage?

The benchmark harness re-encodes all images on every run — fine for offline experiments.
A live search endpoint cannot afford this: encoding 10,000 images takes 30–60 seconds on CPU.
Instead, embeddings are pre-computed once and stored in a database.

### pgvector

pgvector is a PostgreSQL extension that adds:
- A `vector(n)` column type storing a float array of fixed dimension.
- Distance operators: `<->` (L2), `<#>` (negative dot product), `<=>` (cosine).
- Index support: IVFFlat and **HNSW** for approximate nearest-neighbour queries.

The `image_vectors` table uses HNSW with cosine distance. A search query becomes standard SQL:

```sql
SELECT id FROM image_vectors
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### Why pgvector instead of a dedicated vector database (Pinecone, Weaviate, etc.)?

- The project already runs PostgreSQL for benchmark results.
- Same Docker Compose file, same DSN, same backup workflow.
- No additional infrastructure to maintain.
- For our dataset size (hundreds of images) pgvector is more than sufficient.
- Dedicated vector DBs become worthwhile at millions of vectors or with multi-tenancy needs.

---

## 13. Software Design Decisions

### 13.1 Strategy Pattern

The **Strategy Pattern** is a design pattern where a family of algorithms is encapsulated
behind a common interface, and the concrete algorithm is chosen at runtime.

In this project:
- `SearchEngineStrategy` is the interface (abstract base class with `build_index()` and `search()`).
- `FaissFlatEngine`, `BruteForceCosineEngine`, `QuantumMockEngine`, `QiskitSwapTestEngine` are the
  concrete strategies.
- The benchmark harness iterates over a list of strategy instances — it does not know or care
  which engine is running.

This means adding a new search engine requires only implementing the interface. Nothing else
changes. The same pattern is applied to `EmbeddingGenerator` and `BaseDataLoader`.

### 13.2 API-First Design

The backend logic (embedding, search, benchmarking) is designed to be called via a REST API
(FastAPI), not coupled to any frontend. This means:
- The React dashboard can be changed or replaced without touching the backend.
- The same endpoints can be called from a CLI, a notebook, or a mobile app.
- Each component can be tested independently.

### 13.3 Modular Monolith

Everything lives in one git repository, but in strictly separated folders:
`backend/`, `db/`, `frontend/` (planned). There is no microservices overhead, but the internal
boundaries are enforced by the interface/strategy pattern. This is appropriate for an MVP and
academic project.

### 13.4 Configuration-Driven Benchmarking

`benchmarks.yaml` defines which engines, dimensions, and queries to run. CLI flags can override
any value for one-off experiments. This means:
- Adding a new dimension or query requires only a YAML edit, not code changes.
- Reproducibility: the YAML file can be committed and the exact run conditions are documented.

---

## 14. Likely Professor Questions and Answers

**Q: Why compare classical and quantum search?**
A: Quantum algorithms theoretically offer speedups for certain search problems (Grover's algorithm
is O(√N) for unstructured search vs O(N) classically). For vector similarity search the advantage
is less certain and depends on efficient state preparation, which is an open problem. We study
whether quantum approaches can achieve comparable *accuracy* to classical ones, and characterise
the quantum resource cost, to determine whether they are practically relevant at small scale.

**Q: What does CLIP actually learn?**
A: CLIP learns a joint embedding function through contrastive training on 400M image-caption
pairs. The loss pushes matched (image, text) pairs to be nearby in embedding space and unmatched
pairs to be far apart. The result is a universal visual-semantic encoder that generalises to
unseen domains without fine-tuning.

**Q: What is the swap test and why does it measure similarity?**
A: The swap test is a quantum circuit that estimates |⟨ψ|φ⟩|² — the squared inner product of
two quantum states. When states encode L2-normalised vectors as amplitudes, this equals the
squared cosine similarity. The circuit works by using a controlled-SWAP gate and two Hadamard
gates around an ancilla qubit. The measurement statistics of the ancilla encode the overlap.

**Q: What is amplitude encoding and what is its limitation?**
A: Amplitude encoding represents a classical n-dimensional unit vector as the amplitudes of a
log₂(n)-qubit quantum state, requiring exponentially fewer qubits. The limitation is state
preparation: loading an arbitrary classical vector into a quantum register requires O(n) gates
in the worst case, which removes the qubit-count advantage when the bottleneck shifts to gate
count.

**Q: Why does more shots lead to higher accuracy in the quantum engine?**
A: Measuring a quantum circuit once gives a single bit. Estimating P(ancilla=0) requires
running the circuit N times and counting. The standard error in the estimate is 1/√N. With
few shots (e.g., 64) the noise in the similarity estimate is large enough to scramble the
ranking. With 2048 shots the noise is small enough (~2%) that rankings match the classical
result on most queries.

**Q: What is circuit depth and why does it matter?**
A: Circuit depth is the number of sequential gate layers (gates operating on the same qubit
cannot be parallelised). On real quantum hardware, qubits decohere (lose their quantum state)
over time due to environmental noise. Deeper circuits run longer and suffer more decoherence
errors. Circuit depth is therefore a proxy for hardware feasibility on near-term NISQ devices.

**Q: What is the difference between the quantum mock engine and the real Qiskit engine?**
A: The `QuantumMockEngine` computes exact cosine similarity and then adds synthetic Gaussian
noise to simulate shot-based statistical error. It does not run any quantum circuits. The
`QiskitSwapTestEngine` builds and executes real Qiskit circuits on `AerSimulator`, which is a
classical software simulation of a quantum computer. The mock is useful for fast iteration and
studying the noise model; the Qiskit engine demonstrates a real quantum algorithm.

**Q: Why is the Qiskit engine slow in this project?**
A: It runs on AerSimulator, a classical software simulator. Simulating k qubits requires 2^k
complex numbers. For a 128-dim vector we need 15 qubits → 32,768 complex amplitudes per state.
On top of that, the engine runs one full circuit per dataset image per query. For a 100-image
dataset that is 100 circuit executions per query, each with 2048 shots.

**Q: What is FAISS and why is IndexFlatL2 used here?**
A: FAISS (Facebook AI Similarity Search) is a Python library for dense vector similarity search
whose internals use highly optimised SIMD/BLAS routines. `IndexFlatL2` is its exact brute-force
L2 index — it always finds the true nearest neighbours. For our small dataset there is no need
for approximate indices. FAISS is used to demonstrate a production-grade classical baseline
beyond the pure-NumPy brute-force cosine engine.

**Q: Is NDCG the same as weighted accuracy?**
A: The project implements a simplified version. True NDCG uses logarithmic discounting
(1/log₂(rank+1)) and requires a relevance score per result. The weighted accuracy uses
linear weights (1.0, 0.66, 0.33) and a single binary relevance (correct target or not).
The spirit is the same: reward finding the right answer earlier in the list more heavily.

**Q: What is MRR and when is it useful?**
A: MRR (Mean Reciprocal Rank) averages 1/rank across queries, where rank is the position of
the first relevant result. It is most useful when users care primarily about the first result
they see — search engines, question answering, recommendation. A system that always ranks the
correct answer at position 1 gets MRR = 1.0; always at position 2 gets MRR = 0.5.

**Q: How does dataset size affect the quantum engine's performance and resource cost?**
A: The quantum engine runs one circuit per dataset image per query on a classical simulator.
Simulation runtime scales exponentially with qubit count and linearly with shots × dataset size.
A controlled, small initial dataset is therefore necessary for reproducible experiments that
complete in reasonable time. As the dataset grows, the classical overhead of the simulator
grows proportionally, while the qubit count (set by vector dimension, not dataset size) stays
fixed. On real quantum hardware, larger datasets would increase the number of circuit executions
but not the circuit complexity — making dataset size a scheduling concern rather than a
fundamental quantum resource constraint.

**Q: What is the Strategy Pattern and why is it used?**
A: The Strategy Pattern encapsulates a family of interchangeable algorithms behind a common
interface. The benchmark harness calls `engine.build_index()` and `engine.search()` without
knowing the concrete implementation. This makes it trivial to add new engines, swap out the
embedding model, or change the data source — each dimension of variation is isolated behind
its own abstract interface.

**Q: What theoretical quantum advantage exists for similarity search?**
A: Grover's algorithm offers a quadratic speedup (O(√N) vs O(N)) for unstructured search.
For structured vector similarity, algorithms like qRAM-based inner product estimation have
been proposed with polylogarithmic query complexity under certain assumptions. However, these
assume efficient quantum random access memory (qRAM), which does not yet exist as practical
hardware. For near-term NISQ devices, the swap test provides no asymptotic speedup over
classical cosine similarity — the value is in studying the resource requirements and accuracy
characteristics for when better hardware becomes available.
