# Learning Roadmap: Everything You Need to Understand This Project

This document is fully self-contained. Read it from top to bottom and you will have
everything you need to understand Quantum Vector Search — the math, the quantum physics,
the algorithms, and how they all connect to the code.

---

## Part 1 — Mathematical Foundations

### 1.1 Vectors

A **vector** is an ordered list of numbers. We write it as:

```
v = (v₁, v₂, v₃, …, vₙ)
```

Think of it as a point in n-dimensional space, or as an arrow pointing from the origin to
that point. In this project, vectors represent meaning: a sentence and its matching image
are both converted into vectors that sit close together in space.

### 1.2 The Dot Product

The **dot product** of two vectors a and b (of the same length n) is:

```
a · b = a₁b₁ + a₂b₂ + … + aₙbₙ
```

It is a single number. It measures how much the two vectors "point in the same direction."

- If a · b is large and positive → they point in the same direction → similar.
- If a · b ≈ 0 → they are perpendicular → unrelated.
- If a · b is negative → they point in opposite directions.

### 1.3 Vector Length (L2 Norm)

The **length** (or norm) of a vector is:

```
‖v‖ = sqrt(v₁² + v₂² + … + vₙ²)
```

A vector with ‖v‖ = 1 is called a **unit vector**.

**L2 normalisation** means dividing a vector by its length so it becomes a unit vector:

```
v_normalised = v / ‖v‖
```

This project normalises all vectors before any computation. After normalisation, the dot
product equals the cosine similarity (explained next).

### 1.4 Cosine Similarity

**Cosine similarity** measures the angle θ between two vectors:

```
cos(θ) = (a · b) / (‖a‖ · ‖b‖)
```

It ranges from −1 (opposite directions) to 1 (identical direction).

After L2 normalisation (‖a‖ = ‖b‖ = 1):
```
cos(θ) = a · b
```

So on unit vectors, cosine similarity and the dot product are the same thing. This is
why the project normalises vectors first — it simplifies all subsequent math.

### 1.5 Matrices and Matrix Multiplication

A **matrix** is a rectangular array of numbers. A 2×2 matrix looks like:

```
M = | a  b |
    | c  d |
```

Multiplying a matrix M by a vector v gives a new vector — a **linear transformation**:

```
M · v = | a·v₁ + b·v₂ |
        | c·v₁ + d·v₂ |
```

Quantum gates are matrices. Applying a gate to a qubit state is matrix multiplication.

### 1.6 Unitary Matrices

A matrix U is **unitary** if U†U = I, where U† is the conjugate transpose of U and I is
the identity matrix. This means:

1. U always preserves the total probability (it cannot create or destroy probability).
2. U is always reversible (you can always undo it by applying U†).

**All quantum gates are unitary.** This is a fundamental constraint of quantum mechanics —
quantum computation is always reversible.

### 1.7 Complex Numbers

A **complex number** has a real part and an imaginary part:

```
z = a + bi   where i = √(−1)
```

Its **magnitude** is |z| = √(a² + b²). Its **phase** is the angle it makes with the real axis.

Quantum amplitudes are complex numbers. The probability of a state is |amplitude|²,
not the amplitude itself. The phase of an amplitude does not affect probabilities directly,
but it does affect how amplitudes **interfere** with each other — this is the mechanism
that makes quantum algorithms work.

### 1.8 Big-O Notation

Big-O describes how an algorithm's cost grows with input size N:

- O(N) — linear: cost doubles when N doubles. Classical search of an unsorted list.
- O(log N) — logarithmic: cost grows very slowly. Binary search on a sorted list.
- O(√N) — square root: cost grows slower than linear. Grover's quantum search.
- O(N²) — quadratic: cost grows with the square. Naive matrix multiplication.

The entire argument for quantum search is: O(N) classical vs O(√N) quantum.
For N = 1,000,000: classical needs ~1,000,000 steps; quantum needs ~1,000 steps.

---

## Part 2 — Classical Search and Databases

### 2.1 The Search Problem

Given a list of N items and a condition C, find the item(s) that satisfy C.

**Classical unstructured search** (the item could be anywhere, no ordering):
- Check item 1: does it satisfy C? No.
- Check item 2: does it satisfy C? No.
- ...
- Check item k: yes! Done.

On average you check N/2 items before finding the answer. This is O(N).

If the list is **sorted**, binary search finds the answer in O(log N) steps. But sorting
requires knowing the structure. Grover's algorithm achieves O(√N) with **no structure at
all** — an unsorted, unordered database.

### 2.2 Similarity Search (Nearest Neighbour)

Our project does not look for an exact match. It looks for the **most similar** item.

Given a query vector q and a database of n vectors, find the k vectors closest to q.
This is the **k-nearest-neighbour (k-NN)** problem.

**Brute-force approach:** Compute the similarity between q and every database vector.
Cost: O(n · d) where d is the vector dimension. Exact but slow for large n.

**FAISS IndexFlatL2:** Same brute-force logic, but implemented with CPU SIMD instructions
(AVX2, SSE4). Computes many dot products in parallel using hardware vector registers.
Still O(n · d), but with a very small constant factor. Fast for our dataset size.

**HNSW (Hierarchical Navigable Small World):** An approximate method that builds a
multi-layer graph over the vectors:
- Upper layers: few nodes, long-range edges — for coarse navigation.
- Lower layers: many nodes, short-range edges — for fine-grained search.
Search starts at the top, greedily moves toward the query, descends to finer layers.
Cost: O(log n) average. The trade-off: might miss the exact nearest neighbour (approximate).
Used by pgvector for the `image_vectors` table index.

### 2.3 Traditional Database Architecture

A classical database management system (DBMS) consists of:
- **Query Processor:** Compiles SQL, optimises execution plans, evaluates queries.
- **Storage Manager:** Buffer manager (RAM cache), file manager, transaction manager.
- **Disk Storage:** Actual data, indices (B-trees, hash tables), statistics.

Classical databases use binary bits. They are mature, support ACID transactions (Atomicity,
Consistency, Isolation, Durability), and use SQL for queries. Their limitations:
- Unstructured data handling is awkward (requires specialised extensions like pgvector).
- Complex similarity queries on large datasets are expensive.

---

## Part 3 — Embeddings and CLIP

This is the bridge from raw data (text, images) to the vectors the search engines use.

### 3.1 What is an Embedding?

An **embedding** is a learned function that maps an input (text, image, audio, etc.) to a
fixed-length vector. The function is designed so that:

```
similar inputs → nearby vectors
dissimilar inputs → distant vectors
```

A 512-dimensional embedding of "a dog running on a beach" should sit close to the
512-dimensional embedding of a photo of a dog on a beach — even though one is text and
the other is pixels.

### 3.2 Why Vectors?

Once things are vectors, all operations are simple math:
- **Similarity = dot product** (after normalisation).
- **Search = nearest-neighbour query** in vector space.
- **Same math works for any data type** — text, images, audio — as long as they share an
  embedding space.

### 3.3 Transformers (High-Level)

Both the text encoder and image encoder in CLIP are based on the **Transformer** architecture.

A Transformer processes a sequence of tokens using **attention**: each token looks at all
other tokens and decides how much to "attend to" them. This lets the model capture
long-range dependencies (e.g., "not happy" means the word "not" matters for "happy").

The output of a Transformer is a vector that summarises the meaning of the entire input.

### 3.4 Vision Transformer (ViT)

A **Vision Transformer (ViT)** applies the Transformer architecture to images.

Steps:
1. Split the input image (224×224 pixels) into fixed-size **patches** (32×32 pixels).
   A 224×224 image → 7×7 = 49 patches for ViT-B/32.
2. Each patch is **linearly projected** into a vector (a "token").
3. A learnable [CLS] token is prepended to the sequence.
4. All tokens are processed by a standard Transformer (attention layers).
5. The final [CLS] token vector is the image's embedding.

"ViT-B/32" means: Base size model, patch size 32×32.

### 3.5 CLIP: Contrastive Language-Image Pre-training

**CLIP** (published by OpenAI, 2021) has two encoders trained jointly:
- **Image encoder:** ViT-B/32, outputs a 512-dimensional vector.
- **Text encoder:** A smaller Transformer, also outputs a 512-dimensional vector.

**The critical property:** Both encoders project to the **same 512-dimensional space**.
This is what makes cross-modal search possible.

**Training:**
CLIP was trained on ~400 million (image, text caption) pairs scraped from the internet.

For each batch of N pairs, it forms an N×N matrix of cosine similarities between all
image vectors and all text vectors. The **contrastive loss** (InfoNCE) pushes:
- The N diagonal entries (matching pairs) → similarity 1.
- The N²−N off-diagonal entries (non-matching pairs) → similarity 0.

The model learns general visual and semantic concepts — "forest", "ocean", "running" — not
surface-level pixel patterns.

**Zero-shot transfer:** Because CLIP learned general concepts, it works on datasets it has
never seen before. You never need to train it on your specific images.

### 3.6 Dimensionality Truncation

CLIP outputs 512-dimensional vectors. This project truncates to 64 or 128 dimensions to
study how dimensionality affects:
- Search accuracy (MRR)
- Quantum resource cost (qubits, circuit depth)

Truncation is done by keeping the first d components and re-normalising. This works because
CLIP's training objective concentrates the most informative signal in the earlier components.

### 3.7 L2 Normalisation (Why It Is Required)

After CLIP encodes a vector, the project normalises it to unit length:

```
v_normalised = v / ‖v‖
```

Two reasons:
1. **For quantum computing:** Amplitude encoding requires that the vector's squared components
   sum to 1 (|v₁|² + … + |vₙ|² = 1). A unit vector satisfies this exactly.
2. **For classical search:** On the unit hypersphere, cosine similarity equals the dot product
   and is monotonically related to L2 distance. All three metrics give the same ranking.

---

## Part 4 — Quantum Computing Fundamentals

### 4.1 Classical Bits vs Qubits

A **classical bit** is either 0 or 1. Nothing in between.

A **qubit** is a two-level quantum system (e.g., the spin of an electron, the polarisation
of a photon). Its state is written in **bra-ket notation**:

```
|ψ⟩ = α|0⟩ + β|1⟩
```

where α and β are **complex amplitudes**. They must satisfy:

```
|α|² + |β|² = 1
```

When you **measure** the qubit:
- You get 0 with probability |α|²
- You get 1 with probability |β|²
- After measurement, the qubit collapses to that state (superposition is gone)

Before measurement, the qubit is in **superposition** — it simultaneously "encodes" both 0
and 1 with different amplitudes. This is not just probability (like a biased coin) — the
amplitudes are complex and can **interfere** with each other, which is something classical
probability cannot do.

### 4.2 Multiple Qubits

A register of n qubits has 2ⁿ **basis states**:

```
|00…0⟩, |00…1⟩, |00…10⟩, …, |11…1⟩
```

The general state of n qubits is a superposition over all 2ⁿ basis states:

```
|ψ⟩ = α₀|00…0⟩ + α₁|00…1⟩ + … + α_{N-1}|11…1⟩    (N = 2ⁿ)
```

with |α₀|² + |α₁|² + … + |α_{N-1}|² = 1.

**Key insight:** n = 10 qubits encodes N = 1024 states simultaneously.
n = 20 qubits encodes 1,048,576 states. n = 50 qubits encodes ~10¹⁵ states.
This exponential encoding is the source of quantum parallelism.

### 4.3 Quantum Interference

Amplitudes are complex numbers. When paths through a quantum circuit lead to the same
final state, their amplitudes **add together** (interfere):

- **Constructive interference:** Amplitudes add (same sign) → probability increases.
- **Destructive interference:** Amplitudes cancel (opposite signs) → probability decreases.

A quantum algorithm works by engineering the circuit so that:
- Wrong answers interfere **destructively** (their amplitudes cancel out → near 0 probability).
- The right answer interferes **constructively** (its amplitude grows → near 1 probability).

This is exactly what Grover's algorithm does with its diffusion operator.

### 4.4 Quantum Gates

Quantum gates are **unitary matrices** applied to qubits. They transform the amplitude
vector. Because they are unitary, they are always reversible.

**Hadamard gate (H):** The most important single-qubit gate.

```
H = (1/√2) | 1   1 |
            | 1  -1 |
```

Effect:
```
H|0⟩ = (|0⟩ + |1⟩)/√2   →  equal superposition, amplitudes both 1/√2
H|1⟩ = (|0⟩ - |1⟩)/√2   →  equal superposition, but |1⟩ amplitude is negative
```

Applying H to |0⟩ creates equal probability of measuring 0 or 1. But notice the **phase**:
H|1⟩ has a negative amplitude on |1⟩. This phase difference has no effect on a single
measurement, but it matters enormously when gates combine (interference).

**Pauli-X gate (NOT gate):**
```
X|0⟩ = |1⟩,   X|1⟩ = |0⟩
```
Classical NOT. Flips the qubit.

**CNOT gate (Controlled-NOT):**
Two-qubit gate. Has a **control** qubit and a **target** qubit.
```
If control = |0⟩: target unchanged
If control = |1⟩: target flipped (X applied)
```
CNOT creates **entanglement** — the target's state becomes correlated with the control's state.

**CSWAP gate (Controlled-SWAP / Fredkin gate):**
Three-qubit gate: one control, two targets.
```
If control = |0⟩: targets unchanged
If control = |1⟩: the two target registers are swapped
```
This is the core gate of the swap test circuit.

**Toffoli gate (CCNOT):**
Three-qubit gate: two controls, one target. Flips target only if both controls are |1⟩.
Used to implement complex logic in quantum circuits.

### 4.5 Entanglement

When two qubits interact through a gate (e.g., CNOT), their states can become **entangled**:

```
(1/√2)(|00⟩ + |11⟩)  — a Bell state
```

This state cannot be written as a product of two independent qubit states. Measuring the
first qubit (getting 0 or 1) instantly determines the second qubit's value, regardless of
distance. Einstein called this "spooky action at a distance."

Entanglement enables quantum algorithms to create correlations that classical algorithms
cannot efficiently replicate.

### 4.6 Measurement and Collapse

Measuring a qubit in superposition collapses it to a definite state. The outcome is random,
governed by the Born rule: probability = |amplitude|².

This has two critical implications:
1. You can only extract classical information (0 or 1) at the end. You cannot "read out"
   all 2ⁿ amplitudes of an n-qubit register simultaneously.
2. Algorithms must be designed so that after computation, the correct answer has very
   high amplitude, making it the overwhelmingly likely measurement outcome.

### 4.7 Circuit Depth and NISQ

A **quantum circuit** is a sequence of gate operations followed by measurements.

**Circuit depth** is the number of sequential gate layers. Gates that operate on different
qubits can run in parallel (depth = 1). Gates that share a qubit must run sequentially.

**Why depth matters for real hardware:**
Qubits lose their quantum state over time through **decoherence** — interaction with the
environment causes the quantum information to leak away. The time a qubit stays coherent
is characterised by T1 (energy relaxation) and T2 (dephasing) times, measured in
microseconds on current hardware.

Deeper circuits run longer and accumulate more decoherence error. Current **NISQ** (Noisy
Intermediate-Scale Quantum) hardware can reliably execute circuits of depth ~100. Deeper
circuits produce mostly noise.

This is why the project tracks circuit depth as a KPI — it is a proxy for real-hardware
feasibility.

### 4.8 The Walsh-Hadamard Transform

Applying the Hadamard gate to every qubit in an n-qubit register independently is called
the **Walsh-Hadamard transform** (W or H^⊗n).

Starting from the all-zeros state |00…0⟩, the result is:

```
W|00…0⟩ = (1/√N) Σᵢ |i⟩    (N = 2ⁿ)
```

This creates a **uniform superposition**: every basis state |i⟩ has equal amplitude 1/√N,
meaning equal probability 1/N.

The matrix form: W_{ij} = (1/√N) × (−1)^(i·j) where i·j is the bitwise dot product.

This is the initialisation step of Grover's algorithm — it puts the system into an equal
mixture of all N states before the search begins.

---

## Part 5 — Grover's Algorithm

This is the central quantum algorithm for this project.

**Problem:** An unsorted database of N items. Exactly one item satisfies condition C.
Find it. You can evaluate C(s) for any item s in one step.

**Classical solution:** Check items one by one. Average N/2 steps. O(N).
**Grover's solution:** O(√N) steps. Provably optimal for quantum algorithms.

### 5.1 The Oracle

The **oracle** is a black-box quantum operation that "marks" the target state by flipping
its phase:

```
Oracle|s⟩ = −|s⟩    if C(s) = 1 (the target)
Oracle|s⟩ =  |s⟩    if C(s) = 0 (not the target)
```

This is a **phase flip**, not a measurement. The state does not collapse — the oracle just
changes the sign of the target state's amplitude. The rest of the computation can still
use quantum interference.

In practice (as Grover §3 explains), the oracle is implemented so it leaves no trace of
which state was examined, preserving quantum interference.

### 5.2 The Diffusion Operator

After the oracle marks the target, the **diffusion operator** D amplifies it.

D is defined by its matrix:
```
D_{ij} = 2/N    if i ≠ j
D_{ii} = -1 + 2/N
```

Or equivalently: **D = WRW** where W is the Walsh-Hadamard transform and R is:
```
R_{00} = 1  (identity on the |0⟩ state)
R_{ii} = -1 for i ≠ 0  (phase flip on all other states)
```

**Geometric interpretation — "Inversion about average":**

Let α = (1/N) Σᵢ αᵢ be the average amplitude across all N states.

After D is applied, each state's new amplitude is:
```
αᵢ_new = 2α − αᵢ
```

In other words: each amplitude is reflected around the average.

**Why this amplifies the target:**

Before the oracle, all amplitudes are equal at 1/√N.
After the oracle, the target has amplitude −1/√N (phase flipped), others still 1/√N.
Average α ≈ 1/√N (slightly less, because one state is negative).

After the diffusion operator:
- Non-target states: were slightly above average → get slightly reduced.
- Target state: was far below average (negative) → gets boosted to far above average.

Each iteration increases the target's amplitude by approximately 2/√N.

### 5.3 The Full Algorithm

**Step 1 — Initialise:**
Apply Walsh-Hadamard to n qubits (n = log₂N).
Result: uniform superposition, all amplitudes = 1/√N.

**Step 2 — Repeat O(√N) times:**
(a) Apply oracle → flip the target state's amplitude sign.
(b) Apply diffusion operator D → inversion about average.

Each iteration: target amplitude grows by ≈ 2/√N.
After k iterations: target amplitude ≈ (2k+1)/√N.

**Step 3 — Measure:**
After ≈ (π/4)√N iterations (the optimal number), the target amplitude is ≈ 1,
so measurement gives the target with probability ≈ 1.

### 5.4 Why Exactly π/4 × √N Iterations?

The target amplitude follows a sine-like pattern as iterations progress:

```
amplitude after k iterations ≈ sin((2k+1) × arcsin(1/√N))
```

For large N, arcsin(1/√N) ≈ 1/√N. So amplitude ≈ sin((2k+1)/√N).

This reaches 1 (probability = 1) when (2k+1)/√N ≈ π/2, i.e., k ≈ (π/4)√N.

If you iterate too many or too few times, the amplitude is not at its peak and you get the
wrong answer. The number of iterations is exact and must be computed in advance.

### 5.5 The Lower Bound (Why You Cannot Do Better)

Bennett, Bernstein, Brassard, and Vazirani (1996) proved that **any** quantum algorithm
needs at least Ω(√N) queries to find the target with high probability.

Intuition: A quantum algorithm running for T steps can only be sensitive to O(T²) items.
To distinguish "no item satisfies C" from "one item satisfies C", you need T ≥ Ω(√N).

Grover's algorithm achieves O(√N), so it is within a constant factor of optimal.

### 5.6 Connection to This Project

The `QuantumMockEngine` is inspired by the Grover approach:
- Imagine encoding all N database vectors into a quantum superposition.
- Define an oracle that marks the vector most similar to the query.
- Apply Grover's algorithm → O(√N) steps to find the nearest neighbour.

The `QiskitSwapTestEngine` takes a different approach (one circuit per database vector)
and does not achieve the O(√N) speedup. But it uses the same quantum primitives.

The key reason the Grover approach is not implemented in full: **qRAM** (see Part 7).

---

## Part 6 — Amplitude Encoding and the Swap Test

### 6.1 Amplitude Encoding

To use a quantum circuit to compare two vectors, we must first encode the vectors into
quantum states. **Amplitude encoding** does this by mapping vector components to amplitudes.

For a unit vector **v** = (v₁, v₂, …, vₙ) with n = 2^k:

```
|ψ_v⟩ = v₁|00…0⟩ + v₂|00…1⟩ + … + vₙ|11…1⟩
```

All n vector components become the amplitudes of a k-qubit state. This works because:
- Unit vectors satisfy |v₁|² + … + |vₙ|² = 1, exactly the normalisation condition for
  quantum amplitudes.
- We need only k = log₂(n) qubits to represent n numbers. This is exponential compression.

**Example from this project:**
- 64-dimensional CLIP vector → 6 qubits (2⁶ = 64)
- 128-dimensional CLIP vector → 7 qubits (2⁷ = 128)

**The caveat:** Preparing an arbitrary amplitude-encoded state requires O(n) gates.
This is the same cost as classical linear search, which cancels out any Grover advantage
unless you have qRAM (Part 7). This is one of the main findings of the project.

### 6.2 The Swap Test

The **swap test** is a quantum circuit that estimates the squared inner product
|⟨ψ|φ⟩|² of two quantum states |ψ⟩ and |φ⟩.

For unit vectors, ⟨ψ|φ⟩ is the cosine similarity. So the swap test measures similarity.

**The circuit:**
```
ancilla: |0⟩ ──H──●──H──[M]
                   │
state ψ: |ψ⟩ ─────⊗──────────
state φ: |φ⟩ ─────⊗──────────
```
The ● on ancilla with ⊗ on ψ and φ is a CSWAP (Fredkin) gate.

**Step-by-step:**

1. Start: ancilla = |0⟩, registers = |ψ⟩ and |φ⟩.
2. Apply H to ancilla → ancilla becomes (|0⟩ + |1⟩)/√2.
3. Apply CSWAP: if ancilla = |1⟩, swap |ψ⟩ and |φ⟩.
   The joint state becomes: (1/√2)(|0⟩|ψ⟩|φ⟩ + |1⟩|φ⟩|ψ⟩).
4. Apply H to ancilla again.
5. Measure ancilla.

**The math:**
After step 4, the probability of measuring ancilla = 0 is:

```
P(ancilla = 0) = (1 + |⟨ψ|φ⟩|²) / 2
```

Rearranging:
```
|⟨ψ|φ⟩|² = 2 × P(0) − 1
```

For unit vectors, |⟨ψ|φ⟩| = cos(θ), so:
```
cosine_similarity ≈ sqrt(max(0, 2 × P(0) − 1))
```

This is exactly what `qiskit_swaptest.py` computes.

**Qubit count in this project:**
- 64-dim vectors: 6 qubits for |ψ⟩ + 6 qubits for |φ⟩ + 1 ancilla = **13 qubits total**
- 128-dim vectors: 7 + 7 + 1 = **15 qubits total**

**Why the result is squared:**
The swap test gives |⟨ψ|φ⟩|², which is always non-negative. It cannot distinguish between
vectors with positive cosine similarity and vectors with negative cosine similarity (they
both map to a value in [0,1]). For CLIP embeddings (which tend to cluster in the same
hemisphere), this is acceptable.

### 6.3 Shot Noise

A quantum circuit does not give a deterministic result. Each execution (called a **shot**)
measures the ancilla qubit and returns a single bit: 0 or 1.

After N_shots shots, we estimate:
```
P(0) ≈ (count of 0s) / N_shots
```

The statistical error in this estimate is:
```
standard error ≈ 1 / sqrt(N_shots)
```

With N_shots = 2048 (the project default), the error in P(0) is ≈ 0.022. This propagates
through the similarity calculation, causing the quantum engine to occasionally rank items
differently from the ground truth.

**More shots → more accurate → more expensive.** The shots-vs-accuracy trade-off is one
of the project's benchmark dimensions.

---

## Part 7 — Quantum Databases and qRAM

### 7.1 What Makes a Quantum Database Different

A classical database stores binary bits on disk and in RAM. Operations (search, sort, join)
are classical CPU instructions.

A quantum database would store data in qubits and execute quantum algorithms for
queries. Key theoretical advantages:
- Grover's search: O(√N) instead of O(N) for unstructured queries.
- Quantum Fourier Transform: faster certain frequency-domain computations.
- Quantum parallelism: evaluate a function on all inputs simultaneously.

**Architecture of a general-purpose quantum database** (from the IJDE-128 paper):
- **Application Tier:** Regular users, programmers, admin tools.
- **Resource Manager:** Coordinates access to quantum hardware.
- **Quantum Query Optimizer:** Translates queries into quantum circuits.
- **Quantum Data Processor:** Executes circuits on quantum hardware.
- **Error Correction Module:** Detects and corrects quantum errors.
- **Classical Interface:** Bridges quantum results back to classical systems.
- **Classical Database Engine Integration / Hybrid Query Processor:** Most data stays
  classical; only specific subroutines run on quantum hardware.
- **Disk Storage:** Classical persistent storage at the bottom.

This hybrid architecture is the realistic near-term model — quantum accelerates specific
bottlenecks while classical handles everything else.

### 7.2 The qRAM Problem

**qRAM (quantum random access memory)** would be a device that, given a superposition
of indices, returns a superposition of the corresponding data values.

Formally, if the database contains vectors v₀, v₁, …, v_{N-1}:

```
qRAM: Σᵢ αᵢ|i⟩|0⟩  →  Σᵢ αᵢ|i⟩|vᵢ⟩
```

This would load the **entire database** into quantum superposition in O(log N) steps.
With qRAM, Grover's algorithm could find the most similar vector in O(√N) queries.

**Without qRAM**, amplitude encoding each vector individually costs O(n) gates (n = vector
dimension). To encode all N database vectors, that is O(N × n) gates — worse than classical
brute-force search.

**qRAM does not exist in a practical form today.** It is an active research area.

**This is the most important finding of the project:**
The theoretical speedup of quantum search (O(√N)) is currently blocked by the state
preparation cost. The project measures exactly what that costs, and the framework will be
ready to reuse when qRAM becomes available.

### 7.3 Quantum Error Correction

On real quantum hardware, qubits make errors due to:
- **Decoherence:** The qubit interacts with its environment and loses its quantum state.
- **Gate errors:** Each gate operation has a small (~0.1–1%) probability of error.
- **Readout errors:** Measuring the qubit may give the wrong answer.

**Quantum error correction** encodes one "logical qubit" using many "physical qubits"
(typically 50–1000 physical qubits per logical qubit for fault-tolerant computation).
Current NISQ devices (50–1000 qubits total) cannot spare this overhead — they operate
without error correction, which limits circuit depth to ~100 layers.

This is why circuit depth is tracked as a KPI: it is a proxy for decoherence risk.

### 7.4 Current State of Quantum Hardware

Leading platforms (IBM Quantum, Google Quantum AI, IonQ, Rigetti):
- IBM's largest chips: 1000+ physical qubits but ~100 reliable circuit depth.
- Coherence times: T1 = 100–500 microseconds on superconducting qubits.
- Gate fidelity: 99–99.9% for single-qubit gates, 99–99.5% for two-qubit gates.

The project runs all quantum circuits on **AerSimulator** — a classical software simulation
of a quantum computer provided by Qiskit. It is exact (no hardware noise) but uses
exponential classical memory (2ⁿ complex numbers for n qubits). For 15 qubits: 32,768
complex numbers — manageable. For 40 qubits: 10¹² numbers — impossible.

---

## Part 8 — This Project's Engines and Metrics

### 8.1 The Four Search Engines

All four engines implement the same interface: `build_index(vectors)` and `search(query, k)`.

**BruteForceCosineEngine**
- Normalises all vectors to unit length.
- For each query: computes dot product with every stored vector (O(n·d)).
- Sorts descending, returns top K.
- Deterministic. Used as the exact ground truth baseline.

**FaissFlatEngine**
- Stores vectors as a float32 matrix in memory.
- On search: calls FAISS `IndexFlatL2`, which uses SIMD hardware instructions (AVX2/SSE4).
- Still exact brute-force — always finds true nearest neighbours.
- Faster than pure NumPy for larger datasets due to vectorised CPU instructions.
- Classical sentinel: shots = −1, layers = −1.

**QuantumMockEngine**
- Does NOT run real quantum circuits.
- Computes exact cosine similarity classically (as if a perfect quantum computer ran).
- Adds Gaussian noise with standard deviation = layers / max(1, shots).
- Simulates the statistical uncertainty of a shot-based quantum measurement.
- Useful for studying the shots-vs-accuracy trade-off without Qiskit overhead.

**QiskitSwapTestEngine**
- Runs a real swap test circuit on AerSimulator.
- For each (query, database vector) pair: amplitude-encodes both, runs the circuit,
  measures, repeats for the configured number of shots, estimates similarity.
- Cost: n circuits per query (one per database vector). Slow on a simulator.
- This is the only engine doing actual quantum computation.

### 8.2 MRR — Mean Reciprocal Rank

The single cross-engine quality metric.

Each query has exactly one correct image (derived by stripping the "query_" prefix from
the query ID). The engine ranks all database images from most to least similar.

```
Reciprocal Rank of a query = 1 / (rank of the correct image)
```

- Correct image at rank 1 → 1.0
- Correct image at rank 2 → 0.5
- Correct image at rank 5 → 0.2
- Correct image at rank 20 → 0.05

```
MRR = average Reciprocal Rank across all queries
```

MRR directly measures user experience: "on average, how far down the list before hitting
the right result?" The harness ranks ALL database images, not just top-K — so the true
rank is always captured.

### 8.3 Quantum-Specific KPIs

| Metric | What it measures | Why it matters |
|---|---|---|
| Circuit depth | Sequential gate layers per query | Decoherence risk on real hardware |
| Qubit count | Qubits required for one swap test | Hardware allocation cost |
| Shots vs. accuracy | How many measurements to reach target MRR | Time/cost budget on real hardware |

Together: MRR answers "does it work?", circuit depth and qubits answer "at what hardware
cost?", shots vs. accuracy answers "how much measurement budget is needed?"

### 8.4 Why Speed Is Not Compared Across Engines

The quantum engine runs on a classical simulator. Wall-clock time reflects the cost of
classically simulating 2ⁿ amplitudes — not the time a real quantum computer would take.

Comparing speed would be like comparing a horse's speed to a car's speed by timing how
long it takes to *draw a picture* of each one.

What is valid:
- Speed comparison **within** one engine across different dimensions (e.g., dim=64 vs
  dim=128 for the same engine). Same type of computation, different scale.
- Quality (MRR) comparison **across** engines, since accuracy does not depend on simulator overhead.

---

## Part 9 — Putting It All Together

### The Full Pipeline

```
Text query ("a dog on a beach")
        │
        ▼
CLIP text encoder (Transformer)
        │
        ▼
512-dimensional embedding vector
        │
        ▼
L2 normalisation → unit vector
        │
        ▼
Truncate to d dimensions (64 or 128)
        │
        ├──────────────────────────────┐
        │                              │
        ▼                              ▼
Classical engines                 Quantum engines
(BruteForce, FAISS)               (SwapTest, Mock)
        │                              │
Cosine similarity                Amplitude encode
with every stored                both vectors →
image vector                     swap test circuit →
        │                        shots → P(0) →
        │                        similarity
        │                              │
        └──────────┬───────────────────┘
                   ▼
          Rank all images by similarity
                   │
                   ▼
          Find rank of correct image
                   │
                   ▼
          Reciprocal Rank = 1/rank
                   │
                   ▼
          Average over all queries = MRR
```

### The Core Thesis Argument

1. **Grover's algorithm** offers O(√N) quantum search vs O(N) classical — a quadratic speedup.
2. **In this specific problem** (vector similarity search), applying Grover requires loading
   vectors into quantum superposition via amplitude encoding.
3. **Amplitude encoding costs O(n) gates per vector** (n = dimension) — the same as
   classical brute-force search. This cancels the speedup.
4. **qRAM would fix this** — it could load all N vectors in O(log N) steps, restoring the
   O(√N) advantage. qRAM does not exist practically yet.
5. **The swap test (real quantum circuit)** accurately estimates cosine similarity,
   matching classical MRR at the cost of more shots → more accuracy.
6. **Circuit depth and qubit count** quantify exactly what real hardware would need.
7. **Conclusion:** The quantum approach is currently bottlenecked by state preparation,
   not the core algorithm. The project provides the benchmark framework, accuracy baseline,
   and resource cost model that will be needed when hardware improves.

