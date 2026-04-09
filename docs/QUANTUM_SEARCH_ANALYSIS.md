# Quantum Vector Search Analysis

This document resolves the confusion around what quantum vector search can do today, what our benchmarks actually measure, and why this project has value despite qRAM not existing. It covers every discussion point raised during the project's clarification phase and serves as the authoritative reference for our thesis defence.

---

## The Two-Step Problem

Quantum vector search is not one operation — it is two fundamentally separate steps. Conflating them causes all the confusion.

### Step 1: Loading Data into Superposition (the broken step)

To get any quantum speedup in search, all N vectors in the database need to be loaded into quantum superposition simultaneously. A quantum computer in superposition can then evaluate all of them at once rather than one by one.

This step requires **qRAM** (Quantum Random Access Memory) — hardware that can address and retrieve N classical data items as a quantum superposition in O(log N) time.

**qRAM does not exist.** Not on IBM's machines, not anywhere. No working implementation exists at any meaningful scale.

Without qRAM, loading vectors into superposition requires O(N) gate operations — the same number of steps as a classical linear scan. This completely erases the quantum speedup before the actual search even starts:

| Method | Complexity |
|---|---|
| Classical search | O(N) comparisons |
| Quantum search without qRAM | O(N) state preparation + O(√N) Grover search = **still O(N)** |

The swap test circuit and Grover's oracle are real, but they sit downstream of a step that currently cannot be done efficiently.

### Step 2: Grover's Algorithm (the part that works)

Once data is in superposition, Grover's algorithm finds the closest match in O(√N) oracle queries instead of O(N) classical comparisons. This speedup is mathematically proven — it is as solid as any result in computer science.

The catch: this speedup only exists given that Step 1 is already solved. Right now, Step 1 is not solved. So the O(√N) advantage exists in theory but cannot be demonstrated end-to-end on any hardware today.

---

## How Grover's Algorithm Gets O(√N)

Classical search has no choice but to check candidates one at a time. If the answer could be any of N items, you need up to N comparisons in the worst case (average N/2). There is no shortcut because checking one item tells you nothing about the others.

Grover's algorithm exploits a quantum effect called **amplitude amplification**:

### 1. Start in uniform superposition
All N possible answers are represented simultaneously, each with equal probability amplitude of 1/√N.

### 2. Apply the oracle
The oracle is a quantum circuit that knows what a "correct" answer looks like — in our case, a vector that is close to the query. It flips the phase (the sign) of the correct answer's amplitude: +1/√N becomes -1/√N. Measuring at this point would still give you the right answer with the same probability as before, because probability is amplitude squared and (-1/√N)^2 = (1/√N)^2. The flip is invisible to measurement but it has *marked* the answer.

### 3. Apply the diffusion operator
This step inverts all amplitudes around their average. Before the oracle, all amplitudes were equal at 1/√N, so the average was 1/√N. After the oracle, one of them is -1/√N and the rest are still +1/√N, which pulls the average slightly below 1/√N. Inverting around this lower average pushes all the wrong answers slightly down and **amplifies the correct answer significantly up**.

### 4. Repeat
Each iteration of (oracle + diffusion) increases the probability of the correct answer by a meaningful amount. After O(√N) iterations, the correct answer has probability close to 1 and a measurement will find it with high probability.

### Why √N iterations?

The amplitude of the correct answer after k iterations is approximately sin((2k+1) * arcsin(1/√N)). This is maximised when 2k+1 ~ π√N/2, meaning the optimal number of steps is **k ~ π√N/4** — which is O(√N).

Each iteration calls the oracle exactly once. So Grover's algorithm uses O(√N) oracle calls. Classical search uses O(N) comparisons. For 1,000,000 vectors, classical needs up to 1,000,000 comparisons, Grover's needs about 785. That is the speedup.

---

## How Much qRAM Would We Actually Need?

This is where the practical picture gets uncomfortable.

To load N vectors into superposition via qRAM, the most studied theoretical model (bucket-brigade qRAM) requires **O(N) quantum routing nodes** in hardware — not O(log N). The log N advantage is in query time, not in how much physical hardware you need. The qRAM is a quantum tree structure of depth log N that routes queries to the right memory cell, and it has O(N) nodes in total.

| Dataset size | qRAM nodes needed (O(N)) | IBM's largest machine today |
|---|---|---|
| 1,000 vectors | ~1,000 quantum nodes | ~1,100 qubits (IBM Condor) |
| 100,000 vectors | ~100,000 quantum nodes | — |
| 1,000,000 vectors | ~1,000,000 quantum nodes | — |

And this is before error correction. Current quantum hardware has error rates around 0.1-1% per gate. Running a deep circuit without error correction produces garbage. Fault-tolerant quantum computing requires roughly **1,000 physical qubits per one reliable logical qubit** (this ratio will improve, but not by orders of magnitude in the near term).

So for 1,000,000 vectors:
**1,000,000 logical qRAM nodes x ~1,000 physical qubits per logical qubit = ~1 billion physical qubits**

### Why IBM's qubits don't help

IBM's largest machine (Condor) has ~1,100 qubits, but those are **processor qubits** — designed for running gate circuits. qRAM is a completely different hardware architecture. It requires a quantum memory array with a tree-routing structure where all nodes maintain coherence simultaneously during a query. Having processor qubits does not get you closer to qRAM in the same way that having 10,000 transistors does not get you RAM — RAM requires capacitors, decoders, and sense amplifiers, a fundamentally different design. You could scale IBM's processor to a billion qubits and still have no qRAM. The two things are not on the same spectrum.

For our specific use case — image embeddings at 512 dimensions, float32 precision — each vector is 16,384 bits of data. The qRAM needs to store and address all of that. The numbers do not improve when you factor in the data width.

**The short answer:** the qRAM required to run quantum vector search on any interesting dataset (tens of thousands of images and up) is multiple orders of magnitude beyond what exists or is expected to exist within the next decade. This is not a near-term limitation — it is a fundamental hardware gap.

---

## What Changes When qRAM Exists

Everything in Step 1 flips.

| Scenario | State Prep | Grover Search | Total |
|---|---|---|---|
| Without qRAM | O(N) | O(√N) | **O(N)** — no advantage |
| With qRAM | O(log N) | O(√N) | **O(√N)** — genuine quadratic speedup |

For N = 1,000,000:
- Classical: ~1,000,000 comparisons
- Quantum with full qRAM: ~1,000 oracle calls + ~20 for state prep

That is a **real, significant speedup**. The algorithm actually does fewer operations — it is not just faster hardware doing the same work.

### What this means for our project

- The Grover oracle circuit we implement today slots directly into a qRAM-backed pipeline **without modification**. The oracle does not care how the superposition was prepared.
- The simulator benchmarks (measuring oracle query counts at different N) would become achievable in practice, not just in theory.
- The infrastructure we build — the embedding pipeline, the vector database, the search API — is already designed around pluggable search backends. Connecting a qRAM-capable quantum backend would be a backend swap, not an architectural rewrite.

---

## The O(N) State Preparation Problem in Practice

Without qRAM, to run Grover's search on a database of N vectors, each vector must be written into the quantum circuit gate by gate. This takes O(N) gate operations. You cannot load N pieces of information in fewer than N steps if you have to touch each one individually.

In our implementation, state preparation looks like this:

1. We take a small dataset — say 8 vectors (because 8 = 2^3 needs only 3 index qubits).
2. We write a quantum circuit that manually encodes those 8 vectors into a superposition. This circuit has gates proportional to the number of vectors.
3. We run Grover's algorithm on top of that prepared state.

The O(N) cost is already paid before Grover starts. So when we benchmark oracle queries and show O(√N) scaling, we are measuring **only the search step**, not the full pipeline.

**What we do about it:** We do not pretend this cost does not exist. We hardcode state preparation for a small toy dataset, run Grover's search on top of it, measure oracle queries, and document clearly that this measurement isolates the search step. The state prep cost and the qRAM requirement are documented as the reason this cannot be scaled without hardware that does not yet exist.

---

## Simulator vs IBM Hardware

**Primary: the simulator. IBM hardware for one small demonstration only.**

### Why the simulator

The interesting benchmarks — showing that oracle query counts scale as O(√N) across N = 100, 500, 1000, 2000 — require running the algorithm at many different dataset sizes. Each size needs a circuit with more qubits and more depth. IBM's free tier machines are noisy enough that circuits with more than about 5-7 usable qubits produce unreliable results. Queue wait times can be hours.

Even if we got clean results, a dataset of 8 vectors on IBM and 8 vectors on a simulator give you the exact same oracle query count — the scaling comparison is identical. IBM hardware adds nothing to the scaling benchmark.

The simulator (Qiskit Aer) has none of these constraints. No noise, no queue, no circuit depth limits for the sizes we need, and results are deterministic. For the purpose of demonstrating O(√N) oracle scaling, the simulator is strictly better.

### Where IBM adds value

IBM hardware is worth using for exactly one thing: running a tiny end-to-end demonstration (4-8 vectors, manually prepared superposition) on a real quantum computer and comparing the results against the noiseless simulator. This shows two things:
1. That our circuit runs on real qubits at all
2. What quantum noise does to result accuracy

Those are real findings. But they are a single demonstration, not the core benchmark.

### The split

| Platform | Use |
|---|---|
| Simulator | All oracle scaling benchmarks, all O(√N) vs O(N) comparisons, all plots |
| IBM hardware | One noise/accuracy demonstration on a toy dataset, documented as such |

---

## On the Wall-Clock Speed Debate

Comparing wall-clock time between IBM quantum hardware and local classical search is comparing two completely different execution environments. The quantum computer is accessed over HTTP to IBM's data centre, includes queue wait times, measurement shot overhead, and network latency. The classical search runs locally. Any timing result would be meaningless.

### What IS a valid metric

**Oracle query count as a function of N** — how many comparisons does each method make as dataset size grows? Classical: O(N). Grover's: O(√N). This is hardware-independent and directly comparable.

**Scaling curves** — run both methods at N = 100, 500, 1000, 2000 on a simulator, count operations, and plot the curves. The shape of these curves is the finding, not the absolute values.

**Result accuracy** — does quantum search return the same nearest neighbours as classical search? At what noise levels does accuracy degrade? This is measurable on IBM hardware today.

---

## Chunking: Partial qRAM Still Gives Real Speedups

You do not need qRAM large enough for the entire dataset to get a quantum speedup. You can **chunk**.

Say you have 1,000,000 images and qRAM that can hold only 1,000 at a time. Split the dataset into 1,000 chunks of 1,000 images each:

1. Load chunk into qRAM: O(log 1000) ~ 10 operations
2. Run Grover's search within the chunk: O(√1000) ~ 32 oracle calls
3. Extract the best candidate from this chunk
4. Move to the next chunk
5. After all chunks, compare the 1,000 chunk-winners classically: 1,000 comparisons

**Total:** 1,000 chunks x 32 oracle calls = 32,000 operations (plus 1,000 classical at the end)

**Compare to classical linear scan:** 1,000,000 operations. That is a **~31x speedup** using qRAM that only needs to handle 1,000 items at a time.

### The General Formula

For a dataset of N items, chunked into groups of M (with qRAM capable of holding M items):

| Quantity | Value |
|---|---|
| Number of chunks | N / M |
| Oracle calls per chunk | O(√M) |
| Total oracle calls | (N / M) x O(√M) = O(N / √M) |
| Classical comparisons | O(N) |
| **Speedup over classical** | **O(√M)** |

| qRAM capacity (M) | Speedup over classical |
|---|---|
| 100 items | ~10x |
| 1,000 items | ~32x |
| 10,000 items | ~100x |
| 1,000,000 items (full) | ~1,000x |

Larger qRAM = better speedup, but even small qRAM gives a real, meaningful advantage.

### Why Chunking Still Doesn't Work Today

Chunking reduces how much qRAM you need. It does **not** eliminate the qRAM requirement.

Without qRAM, loading a chunk of M vectors into quantum superposition still costs O(M) gate operations. So:

| Scenario | State prep per chunk | Grover per chunk | Total |
|---|---|---|---|
| No qRAM | O(M) | O(√M) | **O(N)** — no speedup |
| qRAM holding M items | O(log M) | O(√M) | **O(N / √M)** — partial speedup |
| qRAM holding all N | O(log N) | O(√N) | **O(√N)** — full speedup |

The moment any working qRAM exists at scale M, you get an O(√M) speedup through chunking. Without qRAM, you get nothing.

### Why This Matters for the Project

This chunking property means quantum vector search is **not an all-or-nothing proposition**. As qRAM hardware improves from hundreds to thousands to millions of addressable items, the quantum speedup for large-scale vector search improves continuously.

The infrastructure we are building — the Grover oracle, the classical pipeline, the pluggable backend design — is already ready for this. When qRAM reaches a practically useful scale, even at 1,000 items, connecting it to our system would immediately yield real performance gains.

---

## What Is the Point of This Project?

We are not going to demonstrate a real end-to-end quantum speedup. That requires qRAM, which does not exist. The project does not claim otherwise.

What we are building and demonstrating:

### 1. The classical infrastructure
A production-quality vector search pipeline — embeddings, vector database, search API, frontend — designed from the start so that a quantum search engine can be plugged in as an alternative backend. This infrastructure has value completely independent of quantum computing.

### 2. A correct Grover oracle implementation, verified
The hard algorithmic work in quantum vector search is designing the oracle circuit: the quantum circuit that, given a query vector in superposition with the database, marks the closest match. We implement this, verify it on a simulator, and demonstrate it on IBM hardware. When qRAM-capable hardware exists, this oracle is the component that unlocks the O(√N) speedup.

### 3. Empirical validation of O(√N) oracle scaling
On a simulator we run Grover's search at different dataset sizes and count oracle queries. We show empirically that our implementation actually scales as O(√N) and not O(N). This validates the theory with real data.

### 4. Accuracy benchmarks on IBM hardware
We run small datasets on a real quantum computer and compare the top-k results against classical search. This measures correctness and noise impact — something no paper can give you from theory alone.

### 5. Honest documentation of the qRAM bottleneck
Most academic papers quietly assume qRAM exists and move on. We document explicitly where the bottleneck is, what it would take to remove it, and what the end-to-end picture looks like with and without it.

### The defensible claim

Our Grover oracle scales as O(√N) on a simulator, produces accurate results on IBM hardware up to noise threshold X, and is ready to be connected to a qRAM-capable backend when that hardware exists.

---

## Implementation Decisions

### Do not implement the IBM quantum engine yet

The simulator covers everything we need for the current phase. IBM hardware adds queue delays, noise management, and integration overhead for a toy-scale demonstration that proves nothing the simulator does not already prove. We will add an IBM backend later, as a single end-to-end noise/accuracy demonstration, when the rest of the system is stable.

### Speed as a KPI: No to wall-clock, yes to oracle count

Raw wall-clock speed is not a valid KPI — the environments are incomparable and without qRAM the end-to-end quantum pipeline is O(N) anyway.

What we measure: **oracle query count as a function of N**. This is the algorithmic speed metric. It is hardware-independent, directly comparable between classical and quantum, and it captures the O(√N) vs O(N) difference. See [BENCHMARK_KPIS.md](BENCHMARK_KPIS.md) for the full KPI specification.

### Implementation phases

**Phase 1 — Simulator (now):**
- `qiskit_grover.py` using AerSimulator as backend (implemented in `backend/src/engines/qiskit_grover.py`)
- `oracle_calls` column in `benchmark_results` (migration 5)
- Operation count scaling section in `generate_report.py`

**Phase 2 — IBM Hardware (later):**
- Run both `qiskit_grover.py` and `qiskit_swaptest.py` on IBM hardware by injecting an IBM backend at construction — no engine code changes required
- Record circuit execution time from job metadata only, not total round-trip time
- Use Qiskit Runtime Session mode to avoid one queue slot per query

---

## Summary

We are building a quantum-ready vector search system in a world where the hardware needed to make quantum search genuinely faster does not exist yet.

That is not a problem. The hardware gap is well-known and documented — every serious paper on quantum machine learning includes a footnote about qRAM. We are working at the actual frontier of where the field is.

The benchmark we present: classical vector search scales as O(N). Our Grover implementation scales as O(√N) in oracle queries, verified empirically on a simulator. The gap between those two curves is the entire argument for why quantum search matters at scale.

The project is not "quantum search beats classical search" — that claim would be false. It is: **here is the complete system, here is the proven quantum advantage in the search step, here is the one missing piece of hardware, and here is what the result looks like the day that piece exists.**
