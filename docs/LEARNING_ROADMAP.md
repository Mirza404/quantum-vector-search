# Learning Roadmap

Everything you need to understand this project — the math, the classical search, the quantum
computing, and how it all connects. This is the single source of truth for learning the theory.
Other docs reference this one; they don't re-explain it.

**Who this is for:** A CS student who can write code but has never studied quantum physics.

**How to read it:** Straight through, in order. Each part builds on the previous one. If a
committee member asks you about any concept in this project, the answer is in here.

---

## Part 1 — The Math

You need four concepts. That's it.

### 1.1 Vectors

A vector is an ordered list of numbers:

```
v = (v₁, v₂, v₃, …, vₙ)
```

In this project, vectors represent meaning. CLIP (the AI model we use) converts a sentence
into a list of 512 numbers, and converts an image into a different list of 512 numbers. If the
sentence describes the image, those two lists end up with similar values. The entire project
is built on comparing these lists.

### 1.2 Dot Product

The dot product of two vectors is:

```
a · b = a₁b₁ + a₂b₂ + … + aₙbₙ
```

Multiply each pair of corresponding components, sum them up. One number comes out.

- Large positive result → the vectors point in the same direction → similar meaning.
- Near zero → perpendicular → unrelated.
- Negative → opposite directions → opposite meaning.

### 1.3 L2 Norm and Normalisation

The length of a vector (its L2 norm) is:

```
‖v‖ = sqrt(v₁² + v₂² + … + vₙ²)
```

A vector with length 1 is a **unit vector**. Dividing any vector by its length makes it a
unit vector — this is called **L2 normalisation**:

```
v_normalised = v / ‖v‖
```

This project normalises all vectors before doing anything else. After normalisation, comparing
vectors becomes simpler because all the metrics below become equivalent.

### 1.4 Cosine Similarity

Cosine similarity measures the angle between two vectors:

```
cos(θ) = (a · b) / (‖a‖ · ‖b‖)
```

Ranges from −1 (opposite) to +1 (identical direction). It ignores how long the vectors are
and only cares about their direction — which is what we want, since direction encodes meaning.

After L2 normalisation (both vectors have length 1), this simplifies to just:

```
cos(θ) = a · b
```

So on unit vectors, **cosine similarity = dot product**. That's why we normalise: one operation
does everything.

**Why this matters for quantum:** The swap test (Part 6) computes |a · b|² — the squared dot
product. On unit vectors, that is the squared cosine similarity. Same quantity, different
computation method.

---

## Part 2 — Classical Search

### 2.1 The Problem

Given a query vector q and a database of N vectors, find the K vectors most similar to q.
This is the **k-nearest-neighbour** problem.

### 2.2 Brute Force

Compare q against every single vector in the database. Compute N dot products, sort by score,
return the top K.

Cost: O(N × d) per query, where d is the vector dimension. Exact — always finds the true
nearest neighbours. This is what `BruteForceCosineEngine` does using NumPy.

### 2.3 FAISS IndexFlatL2

Same brute-force logic, but implemented by Facebook's FAISS library using hardware-level
CPU optimisations (SIMD instructions). Still O(N × d), still exact, but significantly faster
in practice because it processes multiple numbers in a single CPU cycle.

FAISS uses L2 (Euclidean) distance instead of cosine similarity, but after L2 normalisation
these produce the same ranking. `FaissFlatEngine` wraps this.

### 2.4 HNSW (Approximate Search)

For large datasets, brute force is too slow. **HNSW** (Hierarchical Navigable Small World) is
an approximate nearest-neighbour algorithm that builds a multi-layer graph over the vectors:

- Upper layers have few nodes with long-range connections — for fast coarse navigation.
- Lower layers have many nodes with short-range connections — for precise local search.

Average query cost: O(log N). The trade-off: it might miss the exact nearest neighbour.
pgvector uses HNSW for the `image_vectors` table index in this project.

For our small dataset (tens of images), brute force is fine. HNSW becomes important at
thousands to millions of vectors.

---

## Part 3 — CLIP and Embeddings

### 3.1 What Is an Embedding?

An embedding is a function that converts an input (text, image, audio) into a fixed-length
vector. The function is trained so that similar inputs map to nearby vectors and dissimilar
inputs map to distant vectors.

### 3.2 CLIP

**CLIP** (Contrastive Language-Image Pre-training, OpenAI 2021) has two separate encoders
trained together:

- **Image encoder** — a Vision Transformer (ViT-B/32). Takes a 224×224 image, splits it
  into 32×32 pixel patches, processes them through attention layers, outputs a 512-dimensional
  vector.
- **Text encoder** — a smaller Transformer. Takes text, outputs a 512-dimensional vector.

The critical property: both encoders output into the **same** 512-dimensional space. A photo
of a dog and the text "a dog on a beach" end up near each other. This is what makes
cross-modal search (text in, images out) possible.

### 3.3 How CLIP Was Trained

CLIP was trained on ~400 million image-caption pairs from the internet. For each batch of N
pairs, it builds an N×N matrix of cosine similarities between every image and every caption.
The loss function pushes the N correct (image, caption) pairs toward similarity 1 and the
N²−N incorrect pairs toward 0.

The result is a model that understands general visual and semantic concepts. It works on images
it has never seen before — this is called **zero-shot transfer**.

### 3.4 Why We Truncate Vectors

CLIP outputs 512 dimensions. This project truncates to 64 or 128 dimensions to study how
dimensionality affects search accuracy and quantum resource cost.

Truncation keeps the first d components and re-normalises. This works because CLIP's training
concentrates the most informative signal in the earlier components.

### 3.5 Why Normalisation Is Required

After CLIP encodes a vector, the project normalises it to unit length. Two reasons:

1. **Classical search:** On unit vectors, cosine similarity = dot product = monotonically
   related to L2 distance. All metrics give the same ranking.
2. **Quantum search:** Amplitude encoding (Part 6) requires that the vector's squared
   components sum to 1. A unit vector satisfies this.

---

## Part 4 — Quantum Computing Essentials

### 4.1 Qubits

A classical bit is 0 or 1. A **qubit** is a quantum system that can be in a **superposition**
of both:

```
|ψ⟩ = α|0⟩ + β|1⟩
```

The notation `|0⟩` and `|1⟩` is called bra-ket notation — just a convention for writing
quantum states. `|0⟩` means the state "zero", `|1⟩` means "one".

α and β are **amplitudes** — complex numbers that describe how much of each state is present.
They must satisfy:

```
|α|² + |β|² = 1
```

When you **measure** the qubit, the superposition is destroyed. You get 0 with probability
|α|² and 1 with probability |β|². This is not like a coin flip — before measurement, the
amplitudes interact with each other through interference (see 4.3), which is the mechanism
that makes quantum algorithms work.

### 4.2 Multiple Qubits

A register of n qubits has 2ⁿ possible states. The state of the full register is a
superposition over all of them:

```
|ψ⟩ = α₀|00…0⟩ + α₁|00…1⟩ + … + α_{2ⁿ-1}|11…1⟩
```

with all |αᵢ|² summing to 1.

The exponential scaling is the source of quantum computing's power:
- 10 qubits → 1,024 simultaneous states
- 20 qubits → ~1 million states
- 50 qubits → ~10¹⁵ states

One operation on this register affects all 2ⁿ states at once. That is quantum parallelism.

### 4.3 Interference

Amplitudes are complex numbers. When different paths through a quantum circuit lead to the
same state, their amplitudes add:

- If they have the same sign → **constructive interference** → probability increases.
- If they have opposite signs → **destructive interference** → probability decreases.

Every quantum algorithm works by arranging the circuit so that wrong answers interfere
destructively (cancel out) and the right answer interferes constructively (amplifies).

### 4.4 Quantum Gates

Gates are operations on qubits. Every gate is a **unitary transformation** — meaning it is
reversible (you can always undo it) and it preserves the total probability (all |αᵢ|² still
sum to 1 after the gate). This is a fundamental constraint of quantum mechanics.

The gates used in this project:

**Hadamard (H)** — the most important single-qubit gate:
```
H|0⟩ = (|0⟩ + |1⟩) / √2    →  equal superposition
H|1⟩ = (|0⟩ − |1⟩) / √2    →  equal superposition, but with a phase difference
```

Both outputs have equal measurement probability (50/50). The difference is in the sign of
the |1⟩ amplitude. That sign difference has no effect on a single measurement, but it matters
when combined with other gates — this is how interference is engineered.

**CNOT (Controlled-NOT)** — a two-qubit gate with a control and a target:
```
Control = |0⟩ → target unchanged
Control = |1⟩ → target flipped
```

CNOT creates **entanglement** — correlations between qubits that cannot be described by
treating each qubit independently.

**CSWAP (Controlled-SWAP / Fredkin gate)** — a three-qubit gate. One control, two targets:
```
Control = |0⟩ → targets unchanged
Control = |1⟩ → the two targets are swapped
```

This is the central gate of the swap test circuit used in this project.

### 4.5 Entanglement

When qubits interact through gates like CNOT, their states become **entangled**:

```
(1/√2)(|00⟩ + |11⟩)
```

This state cannot be separated into two independent qubit states. Measuring the first qubit
immediately determines the second — if you get 0, the other is 0; if you get 1, the other
is 1. This is true regardless of physical distance.

Entanglement is essential because it creates correlations that quantum algorithms exploit for
computations that classical algorithms cannot replicate efficiently.

### 4.6 Measurement

Measuring a qubit in superposition forces it into a definite state. The outcome is random,
governed by |amplitude|².

Two consequences:
1. You cannot read all 2ⁿ amplitudes out of an n-qubit register. You measure once and get
   one classical result.
2. Algorithms must be designed so that the correct answer has high amplitude before
   measurement, making it the most likely outcome.

### 4.7 Circuits, Depth, and NISQ

A **quantum circuit** is a sequence of gates followed by measurement. **Circuit depth** is the
number of sequential gate layers — gates on different qubits can run in parallel (same layer),
but gates sharing a qubit must run sequentially (different layers).

On real hardware, qubits lose their quantum state over time through **decoherence** —
environmental noise destroys the quantum information. The coherence time on current hardware
is measured in microseconds. Deeper circuits take longer to execute and accumulate more error.

Current quantum hardware is called **NISQ** (Noisy Intermediate-Scale Quantum). NISQ devices
can reliably execute circuits of depth ~100. Beyond that, errors dominate and the output is
noise.

This is why the project tracks circuit depth as a key metric — it directly predicts whether
the algorithm could run on real hardware.

---

## Part 5 — Grover's Algorithm

### 5.1 The Problem

Unsorted database of N items. One item satisfies a condition. Find it.

- **Classical:** check items one by one → O(N).
- **Grover's (1996):** O(√N). Provably optimal — no quantum algorithm can do better.

For 1,000,000 items: classical needs ~1,000,000 checks. Grover's needs ~1,000.

### 5.2 How It Works

**Step 1 — Initialise:** Apply the Hadamard gate to all qubits. This creates a uniform
superposition — every item has equal amplitude 1/√N.

**Step 2 — Repeat ~(π/4)√N times:**

(a) **Oracle:** A quantum operation that recognises the target item and flips the sign of its
amplitude. Nothing else changes — no measurement happens, the superposition is preserved.
The oracle is a black box: it marks the answer without revealing it.

(b) **Diffusion (inversion about average):** Reflect every amplitude around the mean.
The target's amplitude was negative (flipped by the oracle), so it was far below the mean.
After reflection, it ends up far above the mean. Non-target amplitudes, being close to
the mean, barely change.

Each iteration boosts the target's amplitude by roughly 2/√N.

**Step 3 — Measure:** After the optimal number of iterations, the target has amplitude ≈ 1.
Measurement returns it with near-certainty.

### 5.3 Why Exactly π/4 × √N Iterations

The target's amplitude follows a sine curve as iterations progress. It peaks at
(π/4)√N iterations. Too few iterations and the amplitude hasn't peaked. Too many and the
amplitude starts decreasing — you overshoot. The count must be calculated in advance.

### 5.4 Why This Doesn't Directly Help Our Project

Grover's promises O(√N) search, but there's a prerequisite: all N database vectors must
be loaded into quantum superposition simultaneously. This requires **qRAM** — a quantum
memory device that loads N vectors in O(log N) time.

**qRAM does not exist as practical hardware.** It is a theoretical construct.

Without qRAM, you must load each vector individually using amplitude encoding, which costs
O(n) gates per vector (n = vector dimension). Loading all N vectors costs O(N × n) — worse
than classical brute-force search.

This is exactly what our project does: the `QiskitSwapTestEngine` runs one circuit per
database vector, N times total, giving O(N) overall. The quantum part is only the similarity
computation, not the search.

**This is one of the project's most important findings:** the theoretical O(√N) speedup is
blocked by state preparation cost. The project measures exactly what that costs, so the
baseline is ready when qRAM eventually becomes available.

---

## Part 6 — Amplitude Encoding and the Swap Test

This is the core quantum technique used in the project.

### 6.1 Amplitude Encoding

To compute similarity on a quantum circuit, classical vectors must first be converted into
quantum states. Amplitude encoding does this by mapping vector components to qubit amplitudes.

For a unit vector v = (v₁, v₂, …, vₙ) where n is a power of 2:

```
|ψ_v⟩ = v₁|00…0⟩ + v₂|00…1⟩ + … + vₙ|11…1⟩
```

Each of the n components becomes the amplitude of one basis state. Since v is a unit vector,
|v₁|² + … + |vₙ|² = 1, which is exactly the normalisation condition quantum states require.

The key benefit is **exponential compression**: n components are stored in only log₂(n) qubits.

| Vector dimension | Qubits needed |
|---|---|
| 64 | 6 |
| 128 | 7 |
| 512 | 9 |

The caveat: preparing an arbitrary amplitude-encoded state requires O(n) quantum gates. This
is the same cost as classical linear search, which is why the Grover speedup doesn't
materialise without qRAM.

### 6.2 The Swap Test

The swap test is a quantum circuit that estimates |⟨ψ|φ⟩|² — the squared inner product of
two quantum states. When the states encode unit vectors, this is the squared cosine similarity.

**The circuit:**

```
ancilla: |0⟩ ──H──●──H──M
                  │
state ψ: |ψ⟩ ────X────────   (CSWAP targets)
state φ: |φ⟩ ────X────────
```

**Steps:**
1. Prepare ancilla in |0⟩. Load |ψ⟩ (query vector) and |φ⟩ (database vector) into their
   registers via amplitude encoding.
2. Apply Hadamard to ancilla → puts it in superposition.
3. Apply CSWAP: if ancilla is |1⟩, swap the ψ and φ registers.
4. Apply Hadamard to ancilla again.
5. Measure the ancilla.

**The result:**

The probability of measuring 0 is:

```
P(0) = (1 + |⟨ψ|φ⟩|²) / 2
```

Rearranging:

```
|⟨ψ|φ⟩|² = 2 × P(0) − 1
```

The similarity score is then:

```
similarity = √(max(0, 2 × P(0) − 1))
```

This is exactly what `qiskit_swaptest.py` computes.

**Qubit counts in this project:**

Each swap test needs two vector registers plus one ancilla qubit:

| Vector dim | Qubits per register | Total qubits |
|---|---|---|
| 64 | 6 | 6 + 6 + 1 = **13** |
| 128 | 7 | 7 + 7 + 1 = **15** |

**Why squared?** The swap test gives |⟨ψ|φ⟩|², not the signed cosine similarity. It cannot
distinguish positive similarity from negative similarity — both map to a positive value. For
CLIP embeddings (which cluster on the same hemisphere of the unit sphere), this is fine.

### 6.3 Shot Noise

A quantum circuit does not give a deterministic answer. Each execution (a **shot**) measures
the ancilla and returns one bit: 0 or 1. To estimate P(0), you run the circuit many times:

```
P(0) ≈ (count of 0s) / N_shots
```

The statistical error is:

```
standard error ≈ 1 / √N_shots
```

With 2048 shots (the project default), the error in P(0) is ~0.022. This propagates through
the similarity formula and occasionally causes the quantum engine to rank items differently
from the classical ground truth.

More shots → more accurate → more expensive. This trade-off is one of the dimensions the
project benchmarks.

---

## Part 7 — The qRAM Problem

### 7.1 What qRAM Would Do

qRAM (quantum random access memory) would take a superposition of indices and return a
superposition of the corresponding data:

```
Σᵢ αᵢ|i⟩|0⟩  →  Σᵢ αᵢ|i⟩|vᵢ⟩
```

This would load the entire database into quantum superposition in O(log N) steps.
With qRAM, Grover's algorithm could find the most similar vector in O(√N) queries.

Without qRAM, encoding each vector individually costs O(n) gates. Encoding all N vectors
costs O(N × n) — worse than classical search.

### 7.2 Why This Is the Key Finding

The theoretical speedup of quantum search is currently blocked by state preparation cost.
The algorithm itself works correctly (our project verifies this). The missing piece is
efficient data loading.

The project measures the per-circuit resource cost (depth, qubits, shots), establishing
exactly what would be needed when qRAM or equivalent technology becomes available.

### 7.3 Quantum Error Correction (Brief)

Real hardware introduces errors: decoherence, gate errors (~0.1–1% per gate), readout errors.
Quantum error correction encodes one "logical qubit" using many physical qubits
(50–1000 per logical qubit). Current NISQ devices cannot afford this overhead — they operate
without error correction, which limits reliable circuit depth to ~100 layers.

### 7.4 Current Hardware

IBM's largest chips have 1000+ physical qubits but reliable circuit depth around 100.
Coherence times are in the hundreds of microseconds. The circuits in this project (13–15
qubits) are well within qubit count limits, but circuit depth depends on the state
preparation implementation.

The project runs on **AerSimulator** — Qiskit's classical simulation of a quantum computer.
It is mathematically exact (no hardware noise) but exponentially expensive in classical
memory: simulating n qubits requires tracking 2ⁿ complex numbers. For 15 qubits that's
32,768 numbers — manageable. For 40 qubits it would be impossible.

---

## Part 8 — The Project's Engines and Metrics

### 8.1 The Four Engines

All four implement the same interface (`build_index` + `search`), making them interchangeable:

**BruteForceCosineEngine** — Normalises vectors, computes dot products with NumPy, sorts by
score. O(N × d). Exact. Deterministic. This is the ground truth baseline.

**FaissFlatEngine** — Same brute-force approach but using FAISS's SIMD-optimised
implementation. Still exact. Faster on larger datasets.

**QuantumMockEngine** — Computes exact cosine similarity classically, then adds Gaussian
noise with standard deviation = layers / max(1, shots). Simulates the statistical error of
shot-based quantum measurement without running any circuits. Fast, useful for studying the
noise trade-off.

**QiskitSwapTestEngine** — Builds and runs a real swap test circuit on AerSimulator for every
(query, database vector) pair. Amplitude-encodes both vectors, runs the circuit for the
configured number of shots, estimates similarity from measurement statistics. This is the only
engine performing actual quantum computation. Cost: N circuit executions per query.

### 8.2 MRR — The Quality Metric

**Mean Reciprocal Rank:** each query has one correct image. The engine ranks all database
images by similarity. MRR is the average of 1/(rank of correct image) across all queries.

- Correct image at rank 1 → 1.0
- Correct image at rank 2 → 0.5
- Correct image at rank 5 → 0.2

MRR directly measures how far down the results a user scrolls before finding the right answer.
The harness ranks ALL images (no top-K cutoff), so the true rank is always captured.

### 8.3 Quantum-Specific Metrics

| Metric | What it measures | Why it matters |
|---|---|---|
| Circuit depth | Sequential gate layers | Proxy for decoherence risk on real hardware |
| Qubit count | Qubits needed for one swap test | Hardware allocation requirement |
| Shots vs. MRR | Measurement budget for target accuracy | Cost parameter on real hardware |

Together: MRR answers "does the algorithm work?", circuit depth and qubits answer "what
hardware does it need?", shots vs. MRR answers "how many measurements before results are
reliable?"

### 8.4 Why Speed Is Not Compared Across Engines

The quantum engine runs on a classical simulator. Its wall-clock time reflects the cost of
simulating 2ⁿ amplitudes on a CPU — not the time a real quantum computer would take.

Comparing speeds across engines would be meaningless. What is valid:
- **Quality (MRR) across engines** — accuracy does not depend on simulator overhead.
- **Speed within one engine** across dimensions — same computation type, different scale.

---

## Part 9 — The Thesis Argument

The full argument, end to end:

1. **Grover's algorithm** gives O(√N) quantum search vs O(N) classical — a proven quadratic
   speedup.

2. Applying it to vector similarity search requires loading vectors into quantum states via
   **amplitude encoding**.

3. Amplitude encoding costs **O(n) gates per vector** — the same as classical brute-force
   search. This cancels the speedup.

4. **qRAM** could fix this by loading all N vectors in O(log N) steps. qRAM does not exist
   as practical hardware.

5. The **swap test** (a real quantum circuit) accurately estimates cosine similarity on
   AerSimulator, matching classical MRR when given enough shots.

6. **Circuit depth and qubit count** are measured from actual compiled Qiskit circuits,
   giving concrete hardware requirements.

7. **Conclusion:** The quantum approach is algorithmically correct but currently blocked by
   state preparation cost. The project provides the accuracy baseline, resource cost model,
   and benchmarking framework needed to evaluate quantum search as hardware improves.

**What we are NOT claiming:** that quantum is faster, or that it will be. We are establishing
that the algorithm works, measuring what it costs, and identifying exactly what needs to
change (qRAM) before it becomes competitive.
