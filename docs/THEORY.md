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

### Why use amplitude encoding?

Quantum gates operate on qubits, not on classical arrays. Before any quantum algorithm can
compute similarity between two vectors, those vectors must exist as quantum states. Amplitude
encoding is the method used to translate classical data into a form a quantum circuit can
process. It is chosen for three reasons:

**Qubit efficiency.** It is the most compact encoding available. An alternative called basis
encoding stores one component per qubit, meaning a single 64-dimensional vector would require
64 qubits. Amplitude encoding reduces that to just 6 qubits by storing all 64 numbers as the
probability amplitudes of a quantum superposition. This is the exponential compression that
makes quantum approaches to high-dimensional vector search tractable in terms of qubit count.

**Enables quantum inner product computation.** Once two vectors are encoded as quantum states,
the swap test (Section 8) can estimate how similar they are using quantum interference — a
process that has no direct classical circuit equivalent. Amplitude encoding is the necessary
first step that makes the swap test possible.

**Gateway to quantum parallelism.** If state preparation could be done efficiently, you could
load the entire database into a single quantum register simultaneously. A quantum search
algorithm could then find the closest vector in O(√N) operations rather than O(N). Amplitude
encoding is the prerequisite for that potential advantage. This project benchmarks step one —
the hardware and algorithms for the rest are still an open research problem (see Section 14 on
qRAM).

### How amplitude encoding is used in this project

The `QiskitSwapTestEngine` performs amplitude encoding every time it compares two vectors.
It takes the query vector and each database vector, L2-normalises them so all components form
a valid probability distribution (they must sum to 1 in squared magnitude), then loads them
into quantum registers using Qiskit's state initialisation instruction. For a 64-dimensional
vector this packs 64 floating-point numbers into 6 qubits. The swap test circuit is then run
on those two quantum registers to estimate their similarity.

The `QuantumMockEngine` does not perform amplitude encoding — it computes similarity
classically and adds noise afterwards to imitate quantum measurement statistics. Its qubit
count metric models a different hypothetical quantum approach (encoding the entire database
into superposition at once, Grover-style) rather than the per-pair swap test. This is
explained more in Section 9.

### In this project — qubit counts

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
- **Quality** (MRR) — does the quantum engine rank the correct image near the top, same as classical engines?
- **Circuit depth** — how deep a circuit do we need per query? This predicts real-hardware
  feasibility.
- **Qubit count** — how many qubits? This predicts hardware allocation cost.
- **Shots vs. quality** — how many measurements are needed to match classical MRR?
- **Scaling behaviour** — how do these resource costs grow as dimension increases?

---

## 11. Evaluation Metrics

### How retrieval works

Each query maps to exactly one correct image. The target image ID is derived from the query ID
at runtime by stripping the `"query_"` prefix — no separate `target_ids` field is stored in
`ground_truth.jsonc`. For example, query `"query_1000092795"` targets image `"1000092795"`.

The harness always retrieves the **full ranking** — every image in the dataset is ranked from
most to least similar. MRR is then computed over that complete list, giving the true reciprocal
rank of the correct image. There is no top_k cutoff in benchmarking: if the correct image is
at position 15 out of 20, MRR = 1/15, not 0.

`top_k` belongs on the API side as a pagination parameter (`GET /search?q=...&limit=10`) —
it controls how many results to return to the frontend, not how quality is measured.

### 11.1 Mean Reciprocal Rank (MRR)

```
MRR = average of (1 / rank of first correct result) across all queries
```

Asks: "on average, how far down the list do you have to scroll to hit the first correct result?"

- Correct image at rank 1 → contributes 1.0
- Correct image at rank 2 → contributes 0.5
- Correct image at rank 3 → contributes 0.33
- Not found in top K → contributes 0.0

MRR is the most user-focused metric — it directly measures how quickly a user would find a
relevant result. With one correct image per query, MRR is unambiguous: it is always the
reciprocal rank of that single image, averaged over all queries.

### 11.2 Why cross-engine speed comparison is excluded

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

### 13.2 Configuration-Driven Benchmarking

`benchmarks.yaml` defines which engines, dimensions, and queries to run. CLI flags can override
any value for one-off experiments. This means:
- Adding a new dimension or query requires only a YAML edit, not code changes.
- Reproducibility: the YAML file can be committed and the exact run conditions are documented.

### 13.4 Live Search vs. Benchmarking

**Benchmark harness** retrieves the full ranked list and computes MRR over every image. No cutoff — the correct image's true rank is always captured.

**Live API** returns only top K results to the frontend — sending all ranked images on every
search would be impractical. Each result includes a similarity score so the frontend can warn
the user when even the best match scores poorly (the engine always returns *something*, so
without scores there is no way to tell the results are irrelevant).

### 13.5 Benchmark Result Storage and Run Keys

Each row in `benchmark_results` represents one unique combination of
`(query_id, engine_name, dimension, shots, layers)` — the *run key*.
Classical engines store `shots = -1, layers = -1` (a sentinel meaning "not applicable").

**Re-running the same configuration** overwrites the existing row with fresh timings and
scores (`ON CONFLICT ... DO UPDATE`). There is no silent skipping — every run produces
up-to-date data.

**Adding a new shots or layers value** appends new rows for the new combinations without
touching existing ones. Running overnight with many values in `shots_values` and `layers_values`
is safe — each combination is stored independently and re-runnable.

---

## 14. Likely Professor Questions and Answers

**Q: Why compare classical and quantum search?**
A: Quantum algorithms theoretically offer speedups for certain search problems (Grover's algorithm
is O(√N) for unstructured search vs O(N) classically). For vector similarity search the advantage
is less certain and depends on efficient state preparation, which is an open problem. We study
whether quantum approaches can achieve comparable *accuracy* to classical ones, and characterise
the quantum resource cost, to determine whether they are practically relevant at small scale.

*In plain terms:* classical computers are already very good at searching images. This project
asks: can a quantum computer do the same job just as well? We are not claiming quantum is better
— we are measuring whether it is even competitive at small scale, and what it would cost in
quantum resources to get there.

**Q: What does CLIP actually learn?**
A: CLIP learns a joint embedding function through contrastive training on 400M image-caption
pairs. The loss pushes matched (image, text) pairs to be nearby in embedding space and unmatched
pairs to be far apart. The result is a universal visual-semantic encoder that generalises to
unseen domains without fine-tuning.

*In plain terms:* CLIP is trained to know that the word "dog" and a photo of a dog belong
together. It learns this by looking at 400 million images paired with their captions. After
training, you can type a description and CLIP will find matching images — even for things it
has never explicitly seen — because it has learned a shared language for images and text.

**Q: What is the swap test and why does it measure similarity?**
A: The swap test is a quantum circuit that estimates |⟨ψ|φ⟩|² — the squared inner product of
two quantum states. When states encode L2-normalised vectors as amplitudes, this equals the
squared cosine similarity. The circuit works by using a controlled-SWAP gate and two Hadamard
gates around an ancilla qubit. The measurement statistics of the ancilla encode the overlap.

*In plain terms:* the swap test is a quantum trick for checking how similar two vectors are.
You encode both vectors into quantum states, run a small circuit that involves swapping them
(hence the name), and measure one special qubit. The probability of getting a particular
measurement outcome tells you how similar the two vectors were — the more similar, the more
predictable the result.

**Q: What is amplitude encoding, why do we use it, and what is its limitation?**
A: Amplitude encoding is how classical vectors are loaded into a quantum computer. Quantum gates
can only operate on qubits — not on classical arrays — so any quantum algorithm for similarity
search must first translate vectors into quantum states. Amplitude encoding is the standard
method: a normalised n-dimensional vector is stored as the amplitudes of a log₂(n)-qubit
quantum state. This gives two concrete benefits: (1) it requires exponentially fewer qubits
than naive encodings — a 64-dimensional vector needs only 6 qubits instead of 64; (2) once
two vectors are encoded as quantum states, the swap test can estimate their inner product using
quantum interference, which is the core quantum operation in this project. The limitation is
state preparation: loading an arbitrary classical vector into a quantum register requires O(n)
gates in the worst case, which removes the qubit-count advantage when the bottleneck shifts
to gate count. This is an open research problem in quantum machine learning.

*In plain terms:* imagine you have a list of 64 numbers describing an image. To run a quantum
similarity calculation on it, you first need to "pour" those 64 numbers into the quantum
computer. Amplitude encoding is the way you do that pouring — it squeezes all 64 numbers into
just 6 qubits instead of 64, because each qubit can exist in a superposition that simultaneously
encodes multiple values. That compression is the benefit: fewer qubits means the hardware
requirements are manageable. The catch is that the pouring process itself is slow — it takes
as many steps as just comparing the vectors classically. It is like packing a suitcase very
efficiently, but the packing itself takes as long as the whole trip. The hope for the future is
a technology called qRAM that would make the packing instant — but that does not exist yet.

**Q: Why does more shots lead to higher accuracy in the quantum engine?**
A: Measuring a quantum circuit once gives a single bit. Estimating P(ancilla=0) requires
running the circuit N times and counting. The standard error in the estimate is 1/√N. With
few shots (e.g., 64) the noise in the similarity estimate is large enough to scramble the
ranking. With 2048 shots the noise is small enough (~2%) that rankings match the classical
result on most queries.

*In plain terms:* quantum measurement is random — you run the same circuit twice and can get
different results. To get a reliable similarity score you have to run it many times and
average. It is like flipping a coin to estimate if it is fair: flip it 10 times and you might
get 8 heads by chance; flip it 2000 times and the average settles close to the true value.
More shots = more flips = more reliable answer.

**Q: What is circuit depth and why does it matter?**
A: Circuit depth is the number of sequential gate layers (gates operating on the same qubit
cannot be parallelised). On real quantum hardware, qubits decohere (lose their quantum state)
over time due to environmental noise. Deeper circuits run longer and suffer more decoherence
errors. Circuit depth is therefore a proxy for hardware feasibility on near-term NISQ devices.

*In plain terms:* qubits are fragile — they lose their quantum state quickly due to interference
from the environment. Circuit depth is how many steps the computation takes. A shallow circuit
finishes before the qubits fall apart; a deep circuit runs long enough that errors accumulate
and the result becomes unreliable. It is like trying to carry a melting ice cream cone — the
longer you walk, the less ice cream you end up with.

**Q: What is the difference between the quantum mock engine and the real Qiskit engine?**
A: The `QuantumMockEngine` computes exact cosine similarity and then adds synthetic Gaussian
noise to simulate shot-based statistical error. It does not run any quantum circuits. The
`QiskitSwapTestEngine` builds and executes real Qiskit circuits on `AerSimulator`, which is a
classical software simulation of a quantum computer. The mock is useful for fast iteration and
studying the noise model; the Qiskit engine demonstrates a real quantum algorithm.

*In plain terms:* the mock engine cheats slightly — it computes the right answer the classical
way and then adds random noise to imitate what a quantum measurement would look like. It is
fast and useful for testing. The Qiskit engine actually builds and runs quantum circuits, just
on a software simulator instead of real hardware. The mock is "quantum-inspired"; the Qiskit
engine is the real algorithm running on a virtual chip.

**Q: Why is the Qiskit engine slow in this project?**
A: It runs on AerSimulator, a classical software simulator. Simulating k qubits requires 2^k
complex numbers. For a 128-dim vector we need 15 qubits → 32,768 complex amplitudes per state.
On top of that, the engine runs one full circuit per dataset image per query. For a 100-image
dataset that is 100 circuit executions per query, each with 2048 shots.

*In plain terms:* a real quantum chip with 15 qubits processes all 32,768 possible states at
the same time — that is the whole point of quantum computing. A regular CPU has to work through
them one by one. Add in the fact that you run each circuit 2048 times, for every image in the
dataset, and you end up with a huge amount of work for a laptop that is fundamentally not built
for this job.

**Q: What is FAISS and why is IndexFlatL2 used here?**
A: FAISS (Facebook AI Similarity Search) is a Python library for dense vector similarity search
whose internals use highly optimised SIMD/BLAS routines. `IndexFlatL2` is its exact brute-force
L2 index — it always finds the true nearest neighbours. For our small dataset there is no need
for approximate indices. FAISS is used to demonstrate a production-grade classical baseline
beyond the pure-NumPy brute-force cosine engine.

*In plain terms:* FAISS is Facebook's highly optimised library for finding the most similar
vectors in a large list. `IndexFlatL2` is its simplest mode — compare the query against every
single vector and return the closest ones. No shortcuts, no approximations, always the correct
answer. For our small dataset this is fine; at millions of images you would switch to an
approximate index that trades a little accuracy for a lot of speed.

**Q: What is MRR and when is it useful?**
A: MRR (Mean Reciprocal Rank) averages 1/rank across queries, where rank is the position of
the first relevant result. It is most useful when users care primarily about the first result
they see — search engines, question answering, recommendation. A system that always ranks the
correct answer at position 1 gets MRR = 1.0; always at position 2 gets MRR = 0.5.

*In plain terms:* MRR asks "how far down the list does a user have to scroll before hitting
the first correct result?" If the right image is always the very first result, MRR = 1.0. If
it is always second, MRR = 0.5. It is the most practical metric for a real search interface
where users typically stop looking after the first few results.

**Q: How does dataset size affect the quantum engine's performance and resource cost?**
A: The quantum engine runs one circuit per dataset image per query on a classical simulator.
Simulation runtime scales exponentially with qubit count and linearly with shots × dataset size.
A controlled, small initial dataset is therefore necessary for reproducible experiments that
complete in reasonable time. As the dataset grows, the classical overhead of the simulator
grows proportionally, while the qubit count (set by vector dimension, not dataset size) stays
fixed. On real quantum hardware, larger datasets would increase the number of circuit executions
but not the circuit complexity — making dataset size a scheduling concern rather than a
fundamental quantum resource constraint.

*In plain terms:* imagine you have 4 images and 1 query. The quantum engine compares the query
against each image one at a time using a small circuit, repeating each comparison 512 times
(shots) to get a stable answer. With 4 images that is 4 × 512 = 2048 circuit runs — each of
which requires the laptop to simulate quantum behaviour from scratch. With 400 images it becomes
204 800 runs. The circuit itself never gets more complicated as you add images — it is always
the same small circuit comparing one pair of vectors. The slowness comes purely from the
simulator having to fake quantum physics thousands of times, not from the quantum algorithm
itself being fundamentally harder.

**Q: What is the Strategy Pattern and why is it used?**
A: The Strategy Pattern encapsulates a family of interchangeable algorithms behind a common
interface. The benchmark harness calls `engine.build_index()` and `engine.search()` without
knowing the concrete implementation. This makes it trivial to add new engines, swap out the
embedding model, or change the data source — each dimension of variation is isolated behind
its own abstract interface.

*In plain terms:* all four search engines have the same interface — the same function names,
same inputs, same outputs. The benchmark harness does not know or care which engine it is
talking to. Adding a fifth engine requires no changes to the harness at all. It is like a
power strip with standard sockets — any device with the right plug just works.

**Q: Are the simulator results actually meaningful, or is the simulator just faking it?**
A: The Qiskit AerSimulator is mathematically exact — it computes the full quantum state vector
and produces measurement statistics identical to what a perfect, noiseless quantum chip would
produce. This makes it **more accurate but slower** than real hardware: accuracy is higher
because there is no physical noise; speed is lower because a regular CPU has to simulate
quantum behaviour step by step. Real quantum hardware executes circuits much faster but
introduces noise — gate errors, decoherence, crosstalk — that degrades accuracy below the
simulator baseline, with the degradation growing as circuit depth increases. The simulator
therefore represents the best-case ceiling for the algorithm's accuracy. The quantum mock
engine adds configurable artificial noise to explore what happens as you move away from that
ceiling toward realistic hardware conditions.

*In plain terms:* the simulator gives you the right answer slowly; real quantum hardware gives
you a noisier answer quickly. For this project the simulator is ideal — we care about whether
the algorithm works correctly, not about raw execution speed on hardware that does not yet
exist at scale.

**Q: Should we test on a real quantum computer? IBM offers free credits.**
A: Yes, and it would strengthen the project. IBM Quantum (quantum.ibm.com) provides free
access to real quantum hardware. The circuits used here are small — a handful of qubits for
low-dimensional vectors — so jobs fit within the free tier. The interesting result would be
the gap between simulator accuracy and real-hardware accuracy: real hardware noise would push
scores down, and the gap would grow with circuit depth (more layers = more noise). Showing
that gap empirically would directly validate why circuit depth is tracked as a KPI and give
concrete evidence for the conclusion that hardware limitations, not the algorithm, are the
current bottleneck. The practical downside is queue time — free IBM jobs can wait minutes to
hours depending on demand.

*In plain terms:* the simulator is the ideal version of a quantum computer — no mistakes, just
slow. Running the same experiment on a real IBM chip would show how much accuracy you lose to
hardware imperfection today. That comparison — "here is what the algorithm can do in theory,
here is what it actually does on today's hardware" — would be the strongest possible conclusion
for the project.

**Q: What theoretical quantum advantage exists for similarity search?**
A: Grover's algorithm offers a quadratic speedup (O(√N) vs O(N)) for unstructured search.
For structured vector similarity, algorithms like qRAM-based inner product estimation have
been proposed with polylogarithmic query complexity under certain assumptions. However, these
assume efficient quantum random access memory (qRAM), which does not yet exist as practical
hardware. For near-term NISQ devices, the swap test provides no asymptotic speedup over
classical cosine similarity — the value is in studying the resource requirements and accuracy
characteristics for when better hardware becomes available.

**How Grover's algorithm achieves the √N speedup:**
Classical unstructured search checks items one at a time until it finds the answer — O(N) in
the worst case. Grover's algorithm works in three repeating steps:

1. **Superposition** — load all N candidates into a quantum register simultaneously. Every
   candidate starts with equal probability amplitude (1/√N).
2. **Oracle** — apply a quantum operation that marks the correct answer by flipping its
   phase (making its amplitude negative). The oracle does not tell you which item is correct;
   it is defined as "the operation that recognises a match". All N candidates are checked
   simultaneously because they are all in superposition.
3. **Amplitude amplification (Grover diffusion)** — reflect all amplitudes around their
   average. Because the marked item has a negative amplitude, this reflection makes it larger
   relative to the others. Each iteration roughly doubles the gap.

After approximately π/4 × √N iterations, the marked item has near-100% probability amplitude.
A single measurement then returns it. Total cost: O(√N) oracle calls instead of O(N).

**Why this does not directly apply to this project:**
The oracle for similarity search would need to ask "which of these N image vectors is closest
to my query?" — but answering that question requires computing similarity for every image,
which brings you back to O(N). To get the Grover speedup you need quantum random access memory
(qRAM) that can load all N vectors into superposition in O(log N) steps. qRAM is theoretically
described but has never been built at practical scale.

The swap test used in this project measures the similarity between exactly two vectors. It does
not search — it just computes one similarity value. To search through N images the engine calls
it N times, giving O(N) total. The quantum part is only the similarity computation, not the
search itself.

*In plain terms:* imagine you are looking for a specific face in a crowd of 1 million people.
Classically you check one person at a time — up to 1 million checks. Grover's algorithm puts
all 1 million people into a quantum superposition, then runs a trick that gradually makes the
correct person "glow brighter" in probability while everyone else fades. After about 1000
rounds of this trick, the glowing person is almost certainly the right one. That is where the
√1,000,000 = 1000 number comes from.

The reason this project cannot use Grover's speedup is that you need a way to load all 1
million image vectors into the quantum computer at once (qRAM), and that technology does not
exist yet. Instead this project runs the swap test one image at a time — 1 million separate
quantum comparisons — so there is no speedup over just doing it classically. The value of the
project is demonstrating that the quantum similarity computation itself works correctly and
measuring what it costs, so we are ready when the missing piece (qRAM) eventually arrives.
