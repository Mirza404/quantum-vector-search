# Research Questions & Thesis Guide

This document answers three things:
1. What is the thesis question?
2. What do we benchmark and why?
3. How do the results let us draw conclusions?

---

## The Thesis Question

> **On a mathematically exact quantum simulator, can the quantum swap test algorithm perform cross-modal vector similarity search with accuracy comparable to classical search, and what quantum resource cost does it require as a function of vector dimension?**

That is it. One question, two parts: **accuracy** and **cost**.

Everything in this project runs on **AerSimulator** — a classical software simulation of a
quantum computer. AerSimulator is mathematically exact: it produces the same results a
perfect, noiseless quantum chip would produce. This means:
- Our accuracy results are the **best-case ceiling** — real hardware would score lower due
  to physical noise (gate errors, decoherence).
- Our circuit depth and qubit counts are **hardware-agnostic** — they are properties of
  the circuit itself, not the execution platform, so they directly tell us what real
  hardware would need to run this algorithm.

We are NOT asking whether quantum is faster. Speed on a simulator reflects classical
simulation overhead, not quantum execution time. That comparison is meaningless.

We are NOT claiming quantum will ever beat classical search. We are asking whether the
quantum algorithm produces correct results under ideal (simulator) conditions, and what
the circuit requirements look like — so we know what real hardware would need to
reproduce those results.

---

## What Is Already Known vs. What This Project Contributes

This distinction matters for the thesis.

### What is already known from theory

**Quantum could be faster — but only under a condition that does not yet exist.**

Grover's algorithm (1996) proves that quantum computers can search an unstructured list of
N items in O(√N) steps instead of O(N) classically. That is a quadratic speedup, and it is
proven mathematically.

For vector similarity search specifically, theoretical algorithms exist that would give
polylogarithmic query complexity — meaning searching a billion vectors would cost roughly
the same as searching a thousand. But every one of these algorithms requires **qRAM**
(quantum random access memory): a device that loads all N database vectors into quantum
superposition in O(log N) steps.

qRAM has never been built at practical scale. It is a theoretical construct.

**Better Big O does not automatically mean faster wall clock.**

This is a common source of confusion. Wall clock time has two parts:

```
wall clock time = (number of operations) × (time per operation)
```

Big O only describes the first part — how the number of operations grows with N.
Quantum might need O(√N) operations, but if each quantum gate takes 1 microsecond while
a classical CPU executes an operation in 1 nanosecond, that is a 1000× constant factor
disadvantage. At small N, classical wins despite worse Big O. At sufficiently large N,
the better Big O dominates and quantum becomes faster.

So the full picture is:
1. If qRAM is realised → quantum search achieves better asymptotic complexity (O(√N) or
   better vs O(N) classical).
2. That better Big O **would** eventually mean faster wall clock at large enough scale.
3. "Large enough" depends on how big the constant-factor gap is between quantum gate speed
   and classical CPU speed.
4. That gap closes as quantum hardware matures — faster gate times, longer coherence,
   lower error rates.

What is known and what is not:

| Claim | Status |
|---|---|
| Quantum has better theoretical Big O for search | Known, proven (Grover 1996) |
| qRAM would unlock that Big O advantage | Known theoretically |
| qRAM at practical scale | Does not exist yet |
| When quantum gate speed becomes competitive with classical | Unknown, open research |
| Whether quantum wall clock will ever beat classical for this task | Unknown |

**What the thesis can honestly say:**
> If qRAM is realised, quantum vector search would achieve better asymptotic complexity
> than classical search (O(√N) vs O(N)), which at sufficient data scale would translate
> to faster wall clock time — provided quantum hardware gate speeds reach a level
> competitive with classical processors.

This is not overclaiming. The theoretical advantage is real and proven. The conditions
under which it becomes a practical advantage are not yet met — and this project does not
claim otherwise. What this project does is establish the baseline (accuracy and resource
cost) so the conditions can be evaluated concretely when hardware metrics improve.

**Quantum will NOT be more accurate than classical search.**

The swap test computes the same mathematical result as classical cosine similarity. It is
not a different or better similarity measure — it is the same measure implemented using
quantum interference. Shot noise actually makes it *less* accurate than classical unless
enough measurements are taken. Accuracy is never the quantum advantage.

**Accuracy is more nuanced than "quantum is less accurate."**

On AerSimulator (no physical noise) with enough shots, the quantum engine should match
classical rankings exactly — because the underlying math is identical. The only source of
inaccuracy is shot noise from finite measurements:

- Few shots (e.g. 64) → large noise → rankings can be scrambled
- Many shots (e.g. 2048) → small noise → rankings converge to classical
- Infinite shots → identical to classical

So the real accuracy question is: **how many shots do you need before quantum matches
classical, and is that shot budget practical?** That is what sub-question 3 measures.

On real quantum hardware there is an additional accuracy penalty from physical noise
(gate errors, decoherence) that cannot be eliminated by adding more shots. That penalty
grows with circuit depth. The simulator results represent the best-case ceiling; real
hardware would be below it by a gap that depends on hardware quality at the time.

### What this project does NOT claim

- We do not claim quantum search is or will be faster.
- We do not try to discover a new speedup.
- We do not compare wall-clock speeds (that would be meaningless on a simulator).

### What this project actually contributes

The theoretical speedup is known. What is not established is whether the quantum algorithm
produces correct results on a simulated (mathematically exact) quantum circuit, and what
the circuit requirements look like as a function of the data it operates on.

This project answers: **does the algorithm work under ideal conditions, and what circuit
resources does it require?**

That is prerequisite work. Before anyone can claim "quantum search will be faster when
hardware improves", you need to know:
1. The algorithm is correct under ideal (simulator) conditions — verified here via MRR
   comparison against classical engines.
2. The circuit requirements at each scale — circuit depth and qubit count measured here
   from the actual compiled Qiskit circuit. These are the minimums real hardware must meet.
3. The exact bottleneck — state preparation costs O(n) gates, the same as classical.
   This means even with better hardware, the speedup only materialises if qRAM is solved.

The benchmarking framework, accuracy baseline, and resource cost model established here
are the reference point for evaluating quantum search when hardware does eventually improve.

## Why This Question Is Worth Asking

Classical vector search (NumPy cosine, FAISS) is already very good. There is no reason to
replace it today. The value of this project is:

1. The quantum algorithm might be wrong or too noisy to produce useful rankings. We need
   to check that first before any other discussion is possible.
2. Quantum hardware is improving. The qubit counts and circuit depths measured here tell
   us exactly what kind of hardware would be needed to run this algorithm at scale.
3. State preparation costs O(n) gates — the same as classical search. This is the most
   important finding: it identifies exactly why quantum search cannot yet offer a speedup,
   and what would need to change (specifically, efficient qRAM).

---

## The Three Sub-Questions and How We Answer Them

### Sub-question 1: Does the quantum algorithm produce correct results?

**What we measure:** MRR (Mean Reciprocal Rank) for each engine across all queries.

**What "correct" looks like:** `qiskit_swap_test` MRR is close to `brute_force_cosine` MRR.
The brute-force cosine engine is the ground truth — it is deterministic and exact.

**What the result means for the thesis:**
- If MRR matches → the quantum swap test circuit produces correct results on AerSimulator
  at our chosen shot count. This is the best-case ceiling — real hardware would add
  physical noise on top of shot noise, so real-hardware accuracy would be ≤ this.
- If MRR is significantly lower → shot noise is already scrambling rankings even on the
  ideal simulator. We need more shots or there is a bug in the circuit.

**Engines involved:** `brute_force_cosine`, `faiss_flat_l2`, `quantum_mock_sampler`, `qiskit_swap_test`

The mock sampler (`quantum_mock_sampler`) is a sanity check — it adds synthetic noise to
classical cosine similarity to model shot error without running real circuits. If the mock
and the real Qiskit engine produce similar MRR, the noise model is valid. If they differ,
the real circuit has additional overhead not captured by the noise model.

---

### Sub-question 2: What does the quantum approach cost in hardware resources?

**What we measure:** Circuit depth and qubit count for each dimension.

| What it is | Why it matters |
|---|---|
| **Circuit depth** | Deeper circuits run longer and accumulate more decoherence errors on real hardware. Current NISQ devices handle roughly ~100 gate layers reliably. |
| **Qubit count** | More qubits = harder to allocate on real hardware. Most public quantum computers today have 100–1000 qubits, but coherence drops with count. |

**What "acceptable" looks like:** Circuit depth stays below ~100, qubit count stays in the
tens for the dimensions we test (64-dim → 13 qubits, 128-dim → 15 qubits).

**What the result means for the thesis:** We report the exact circuit depth and qubit count
at each dimension. This gives a concrete claim: "to run quantum vector search on 128-dim
CLIP embeddings, a quantum computer needs at least 15 qubits and a coherence time sufficient
for a circuit of depth D." We compare that against what current hardware offers.

**Engines involved:** `qiskit_swap_test` (real extracted circuit metrics), `quantum_mock_sampler` (theoretical estimates)

---

### Sub-question 3: How many measurements (shots) are needed before quality is acceptable?

**What we measure:** MRR at each shots value (512, 1024, 2048, 4096).

**What the result means for the thesis:** We measure this on AerSimulator — the shot noise
model is statistical (1/√shots error) and is identical on the simulator and on real
hardware. So this curve directly transfers: it gives the minimum shot budget needed to
reach a target accuracy under ideal conditions. On real hardware, physical noise would
require even more shots to compensate, so our simulator curve is a lower bound on the
real-hardware shot requirement. On real hardware, every additional shot also costs time
and money, making this a concrete cost parameter for any real deployment.

**Engines involved:** `quantum_mock_sampler`, `qiskit_swap_test`

---

### Bonus: How do all of the above scale with dimension?

We run each engine at dim=64 and dim=128. This gives us two data points for:
- How MRR changes as dimension increases (does accuracy hold up?)
- How circuit depth grows with dimension (linear? worse?)
- How qubit count grows (log₂(dim) + 1 ancilla — we can verify the theory matches practice)

This is the scaling analysis section of the thesis.

---

## How to Read the Benchmark Report

The benchmark report (`backend/docs/benchmark_report.md`) maps directly to the thesis:

| Report section | Answers sub-question |
|---|---|
| Results Summary / Quality KPIs by Engine | Sub-question 1 (accuracy) |
| Head-to-Head Quality Comparison | Sub-question 1, per-query detail |
| Quantum Circuit Complexity | Sub-question 2 (resource cost) |
| Quantum: Shots vs. Quality | Sub-question 3 (measurement budget) |
| Quality by Dimension | Scaling analysis |
| Speed Scaling by Dimension | Intra-engine scaling only — not cross-engine |

---

## The Thesis Conclusion Template

Once benchmarks are run with all engines enabled, the conclusion writes itself:

1. **Accuracy (on AerSimulator — best-case ceiling):** The `qiskit_swap_test` engine
   achieved MRR of X.XXX on AerSimulator, compared to X.XXX for `brute_force_cosine`.
   The quantum algorithm [matches / falls short by N%] at [shot count] shots on AerSimulator,
   which includes shot noise (1/√shots statistical error) but no physical hardware noise
   (gate errors, decoherence). Real quantum hardware would score lower because physical
   noise adds on top of shot noise.

2. **Resource cost:** At 64-dim, the swap test requires 13 qubits and a circuit depth of D.
   At 128-dim, it requires 15 qubits and depth D'. This grows [as expected / faster than expected]
   with dimension.

3. **Shot budget:** MRR reaches an acceptable threshold at N shots. Below that, shot noise
   degrades ranking quality significantly.

4. **Bottleneck:** State preparation costs O(n) gates — the same as classical cosine search.
   This eliminates any asymptotic speedup. The quantum similarity computation itself is
   correct; the unsolved problem is loading data into quantum registers efficiently (qRAM).

5. **Implication:** Quantum vector search is algorithmically correct but currently impractical
   at scale due to (a) state preparation overhead and (b) the qubit and circuit depth
   requirements of near-term hardware. The benchmarking framework established here provides
   the baseline for re-evaluation as hardware improves.

6. **The accuracy-speed trade-off framing:** This project's findings fit into a trade-off
   already well-understood in classical search. Production systems routinely sacrifice some
   accuracy for speed — HNSW and IVF approximate indices are standard practice precisely
   because exact search is too slow at scale, and a small accuracy loss is acceptable.
   Quantum vector search, if qRAM is realised, would represent the same kind of trade-off
   at a different scale: some accuracy cost from shot noise and hardware imperfection, in
   exchange for better asymptotic time complexity on very large datasets. This is not a
   weakness of the quantum approach — it is the same engineering decision that already
   drives classical ANN adoption. The contribution of this project is quantifying the
   accuracy cost side of that trade-off concretely, so the trade-off can be evaluated
   honestly when the speed side (qRAM, mature hardware) becomes available.
