# Search Engines - Plain Language Guide

Five engines. One job: **given a text description, find the most matching image.**

Every engine receives the same input - a list of ~512 numbers (a "vector") representing
your query - and searches for the most similar vector in the database. They differ in
*how* they search.

---

## What is a vector, quickly

When CLIP processes the text "a dog on the beach", it outputs a list of 512 numbers,
something like `[0.12, -0.84, 0.03, ...]`. An image of a dog on a beach gets a similar
list. The closer those two lists "point in the same direction", the more semantically
similar they are. This closeness is what all five engines measure.

---

## 1. Brute Force Cosine

**One sentence:** Check every single image, one by one, score it, keep the best.

### The analogy

You walk into a library of 10,000 books looking for the one most similar to a book you
love. Brute force means you pick up every single book, read the blurb, give it a score,
put it back, and move to the next one. Exhausting. But you *never miss the best book.*

### How similarity is measured

The "score" is the cosine of the angle between two vectors. Think of two arrows
pointing out from the same origin. A small angle between them = they point in roughly
the same direction = high similarity. A right angle = completely unrelated.

![Angle between two vectors - cosine similarity](https://upload.wikimedia.org/wikipedia/commons/7/76/Inner-product-angle.svg)

> cos(0°) = 1.0 (identical direction, perfect match).
> cos(90°) = 0.0 (perpendicular, no relation).

Because all our vectors are normalised to length 1 first, the denominator of the
formula disappears and this reduces to a simple dot product - fast to compute.

### Complexity

**O(N)** - for N images you do N comparisons. Double the dataset, double the work.

### Role in this project

This engine is the **ground truth**. Every other engine's quality (MRR score) is
measured against brute force results. If brute force ranks image A first, that is the
correct answer.

---

## 2. FAISS Flat L2

**One sentence:** Still checks every vector like brute force, but measures distance
differently (L2 instead of cosine) and uses CPU hardware acceleration to compute many
distances at once.

### The important distinction

The algorithm is *not* the same as brute force. Brute force computes cosine similarity.
FAISS Flat L2 computes L2 (Euclidean) distance - the straight-line distance between
two points in space.

They happen to produce **identical rankings** on our data - but only because all
vectors are normalised to length 1 before storage. On unit-length vectors, minimising
L2 distance is mathematically the same as maximising cosine similarity:

```
||a - b||² = 2 - 2·cos(θ)
```

Smaller L2 = smaller angle = higher cosine. The rankings come out the same.
If the vectors were *not* normalised, FAISS and brute force would return different
orderings. The equivalence is a consequence of our normalisation step, not a general
property of the two metrics.

### The analogy

Same library as before - you still check every book. But you are now measuring
"physical distance between two summaries on a page" rather than "the angle they make."
On this particular library's shelves (where everything is normalised), the closest book
by distance is always the same as the most aligned book by angle. Different ruler, same
answer - here.

The other difference: your eyes can read 8 blurbs at once. This is SIMD (Single
Instruction, Multiple Data) - modern CPUs (AVX2/AVX-512) perform the same arithmetic
on 8 or 16 numbers simultaneously instead of 1.

### How similarity is measured

![L2 / Euclidean distance between two vectors](https://upload.wikimedia.org/wikipedia/commons/5/55/Euclidean_distance_2d.svg)

> ||a - b||² = 2 - 2·cos(θ). On normalised vectors, smallest distance = highest cosine.
> Different ruler, same ranking - but only because of normalisation.

### Complexity

**O(N)** - still checks every vector, but with SIMD doing 8+ at a time the wall-clock
time is much lower than brute force for large datasets.

### Role in this project

Production-grade reference for exact search - when correctness is non-negotiable
(deduplication, compliance, offline batch). At scale, production systems switch to
approximate indexes like HNSW. Meta built FAISS and uses it internally with those
approximate indexes, not Flat.

---

## 3. Qiskit Swap Test

**One sentence:** Use a quantum circuit to estimate how similar two vectors are by
running a probabilistic experiment many times and averaging the results.

### The analogy

You have two buckets of paint - one from image A, one from your query. You want to
know how similar the colours are without permanently mixing them. Your method: scoop a
tiny sample from each bucket, combine them for a moment in a test tube, shake, and
look. If the colour comes out uniform, they were similar. If it looks streaky, they
were different. You do this hundreds of times and count the "uniform" results.

Each test-tube experiment is one **shot**. The fraction of uniform results encodes the
similarity. More shots = more accurate estimate.

### How the circuit works

The circuit has three parts:
- Two **registers** - each holds one vector encoded as quantum amplitudes
  (log₂(dim) qubits per register; at dim=64 that's 6 qubits per register)
- One **ancilla qubit** - the "referee"
- The sequence: Hadamard on ancilla → controlled-SWAP between registers → Hadamard →
  measure ancilla

The math: `P(ancilla = 0) = (1 + |overlap|²) / 2`

You run the circuit many times (shots) and count how often the ancilla measures 0.
That fraction tells you the overlap between the two vectors.

![Quantum swap test circuit](https://upload.wikimedia.org/wikipedia/commons/d/d6/Quantum-swap-test-circuit-correct.png)

> Ancilla qubit on top. Two vector registers in the middle. The controlled-SWAP is the
> key gate. Measurement result encodes similarity.

### Complexity

**O(N) circuits** - you still run one circuit per candidate image. No speedup over
classical. The swap test is a similarity *estimator*, not a search algorithm.

### Role in this project

Maps the **shots-to-quality curve**: how many shots do you need before the MRR (quality
score) converges to brute force? At what point is the quantum estimate accurate enough
to be useful? We also verify the circuit produces the mathematically correct overlap.

---

## 4. Qiskit Grover Oracle

**One sentence:** Use quantum superposition and interference to find the best match in
O(√N) steps instead of O(N) - the central quantum speedup this project studies.

### The analogy - the maze

A room with 1,000 locked doors. One door leads to the prize.

**Classical search:** Try door 1 (locked), try door 2 (locked), ... on average you
try 500 doors before finding the prize.

**Grover's search:**
1. Quantum mechanics lets you "be in front of all 1,000 doors at once" (superposition).
2. A special oracle marks the prize door with a phase flip - like secretly painting it
   red without you being able to see it yet.
3. A diffusion step uses quantum interference to cancel out all the non-prize doors
   (they destructively interfere) and amplify the prize door (constructive interference).
4. After about √1,000 ≈ 31 rounds of oracle + diffusion, you collapse to the prize door.

31 attempts instead of 500. That is the O(√N) speedup.

### How the circuit works

1. **Hadamard gates** put all N states into equal superposition
2. **Oracle** flips the phase of the target state (the closest matching vector)
3. **Diffusion operator** reflects all amplitudes around their average - this amplifies
   the marked state and suppresses everything else
4. Repeat steps 2+3 for `floor(π·√N / 4)` iterations
5. **Measure** - target state has probability close to 1

![Grover's algorithm circuit](https://upload.wikimedia.org/wikipedia/commons/a/ae/Grovers_algorithm.svg)

> Oracle marks the target; diffusion amplifies it. Each repetition boosts the target
> amplitude further. After O(√N) rounds, measurement almost certainly returns it.

| Dataset size | Classical comparisons | Grover oracle calls |
|---|---|---|
| 100 | 100 | 8 |
| 1,000 | 1,000 | 25 |
| 10,000 | 10,000 | 79 |
| 1,000,000 | 1,000,000 | 785 |

### The critical catch: qRAM

Grover needs all N vectors loaded into superposition simultaneously. Loading them from
classical memory takes O(N) operations - wiping out the speedup. The solution would be
**qRAM** (quantum RAM that can load N items in O(log N) steps), but this hardware does
not exist. See `QUANTUM_INTUITION.md` and `QUANTUM_SEARCH_ANALYSIS.md` for the full
story.

### Role in this project

The central experiment. We run real Grover circuits on AerSimulator and verify the
oracle call count follows `floor(π·√N / 4)` empirically across different N values.
The speedup is real - we just also explain honestly why it doesn't win in practice yet.

**Important caveat - the oracle is classically pre-specified.** For Grover to work as
actual search, the oracle circuit would need to *compute* which vector is closest: load
all N database vectors into quantum registers simultaneously, evaluate distances to the
query in superposition, and flip the phase of the minimum. That computation requires
qRAM to load the N vectors in O(log N) steps - otherwise loading alone costs O(N) and
wipes out the speedup.

Since qRAM does not exist, this simulation does the next best thing: find the nearest
neighbour classically with brute force, then construct an oracle that marks exactly that
index. The quantum amplitude amplification runs correctly and the oracle call count
follows the `floor(π·√N / 4)` curve. What is being verified is the *scaling behaviour*
of the algorithm, not a search that could replace the classical step.

---

## 5. HNSW

**One sentence:** Navigate a multi-layer map from coarse to fine, reaching the nearest
neighbour in O(log N) hops - no quantum hardware required.

### The analogy

Finding a specific address in an unfamiliar city.

- **Brute force:** Check every house on every street in the city.
- **HNSW:** Start at the airport (top layer - a handful of landmarks far apart). Drive
  to the landmark nearest your destination. Zoom into the neighbourhood map (middle
  layer). Walk street by street (bottom layer) to the exact address.

Each layer is sparser than the one below. You zoom in through them, each time already
close to your target. You never need to scan the whole city.

### How it actually works

The dataset is organised as a multi-layer graph:
- **Top layers:** few nodes, long-range connections - fast coarse navigation
- **Bottom layer:** all nodes, short-range connections - precise local search
- **Query:** enter at the top, greedily move toward the query vector, drop to the next
  layer when you can't get closer, repeat until you reach the bottom

![HNSW multi-layer graph structure](https://upload.wikimedia.org/wikipedia/commons/2/28/Hierarchical_Navigable_Small_World_(HNSW).png)

> Sparse top layers for fast long-range jumps; dense bottom layer for local precision.
> The query descends through the hierarchy in O(log N) total hops.

### Is "approximate" a problem?

HNSW occasionally misses the single absolute best match. In practice it achieves
95--99%+ recall, meaning if the true best match is image A, HNSW returns image A almost
always. For image search users the difference between rank-1 and rank-1 with a 0.5%
miss rate is invisible.

### The punchline: why HNSW beats Grover

| Method | Complexity | Requires |
|---|---|---|
| Brute force / FAISS | O(N) | Nothing |
| Grover + ideal qRAM | O(√N) | qRAM (does not exist) |
| **HNSW** | **O(log N)** | **Nothing** |

O(log N) grows slower than O(√N). At N = 1,000,000:
- HNSW needs ~20 operations
- Grover with ideal (non-existent) qRAM needs ~785 oracle calls

**HNSW wins by ~40x on a standard laptop today, with zero exotic hardware.**

This is not a knock against quantum computing in general - it is a specific statement
about this problem at this point in hardware history. Grover's speedup is real and
proven. The issue is that classical algorithms for approximate nearest-neighbour search
have already reached O(log N), which Grover cannot beat even with ideal conditions.

### Role in this project

Implemented as the 5th benchmarking engine: `FaissHnswEngine` in
`backend/src/engines/faiss_hnsw.py`, wrapping FAISS `IndexHNSWFlat`. Its purpose is to
complete the comparison: not just "quantum vs brute force" but "quantum vs the actual
production standard."

On the current 20-image dataset, HNSW is expected to match the exact FAISS L2 ranking
and MRR. The graph is too small to expose the approximation trade-off; that only becomes
meaningful at thousands of vectors and above.
