# Research Questions & Thesis Guide

What the thesis asks, what we benchmark, and how the results lead to conclusions.
For the underlying theory, see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## The Thesis Question

> **On a mathematically exact quantum simulator, can the quantum swap test algorithm perform
> cross-modal vector similarity search with accuracy comparable to classical search, and what
> quantum resource cost does it require as a function of vector dimension?**

One question, two parts: **accuracy** and **cost**.

Everything runs on **AerSimulator** — mathematically exact, no hardware noise. This means:
- Accuracy results are the **best-case ceiling** — real hardware would score lower.
- Circuit depth and qubit counts are **hardware-agnostic** — properties of the circuit, not
  the execution platform.

We are NOT asking whether quantum is faster. We are NOT claiming quantum will beat classical.
We are asking: does the algorithm work under ideal conditions, and what does it cost?

---

## What Is Known vs. What This Project Contributes

| Claim | Status |
|---|---|
| Grover's gives O(√N) quantum search | Proven (1996) |
| qRAM would unlock that advantage for vector search | Known theoretically |
| qRAM at practical scale | Does not exist |
| When quantum gate speed becomes competitive with classical | Unknown |
| Whether quantum wall clock will ever beat classical for this task | Unknown |

**What theory establishes:** Quantum search has better asymptotic complexity, but only with
qRAM. Better Big O does not automatically mean faster wall clock — constant factors (gate
speed vs CPU speed) determine the crossover point.
See [LEARNING_ROADMAP — Parts 5 and 7](LEARNING_ROADMAP.md#part-5--grovers-algorithm).

**What theory also establishes:** The swap test computes the same mathematical result as
classical cosine similarity. Quantum is not a better similarity measure — it is the same
measure via a different mechanism. Shot noise makes it *less* accurate unless enough
measurements are taken. With enough shots on AerSimulator, it converges to classical results.

**What this project contributes:**
1. Empirical verification that the swap test produces correct results on AerSimulator.
2. Measured circuit depth and qubit count at each dimension from actual compiled circuits.
3. Identification of the bottleneck: state preparation costs O(n) gates, same as classical.
4. A benchmarking framework ready for re-evaluation when hardware improves.

**What this project does NOT claim:**
- Quantum search is or will be faster.
- We discovered a new speedup.
- Wall-clock speed comparison (meaningless on a simulator).

**What the thesis can honestly say:**
> If qRAM is realised, quantum vector search would achieve better asymptotic complexity
> (O(√N) vs O(N)), which at sufficient data scale would translate to faster execution —
> provided quantum hardware gate speeds reach a level competitive with classical processors.

---

## The Three Sub-Questions

### Sub-question 1: Does the quantum algorithm produce correct results?

**Measure:** MRR for each engine across all queries.

**"Correct" means:** `qiskit_swap_test` MRR is close to `brute_force_cosine` MRR.
Brute-force cosine is the ground truth — deterministic and exact.

**Result interpretation:**
- MRR matches → swap test circuit is correct at our shot count. This is the best-case
  ceiling; real hardware would add physical noise.
- MRR significantly lower → shot noise is scrambling rankings. Need more shots or there
  is a bug.

**Engines:** `brute_force_cosine`, `faiss_flat_l2`, `quantum_mock_sampler`, `qiskit_swap_test`

The mock sampler is a sanity check: if it and the Qiskit engine produce similar MRR, the
noise model is valid. If they differ, the real circuit has additional overhead.

---

### Sub-question 2: What does the quantum approach cost in hardware resources?

**Measure:** Circuit depth and qubit count for each dimension.

| Metric | Why it matters |
|---|---|
| Circuit depth | Deeper circuits accumulate more decoherence. NISQ devices handle ~100 layers. |
| Qubit count | More qubits = harder to allocate. Current QPUs: 100–1000 qubits. |

**"Acceptable" means:** Depth below ~100, qubits in the tens (13 at dim=64, 15 at dim=128).

**Result interpretation:** Concrete claim — "to run quantum vector search on 128-dim
embeddings, hardware needs at least 15 qubits and coherence time sufficient for depth D."

**Engines:** `qiskit_swap_test` (real metrics), `quantum_mock_sampler` (theoretical estimates)

---

### Sub-question 3: How many shots are needed for acceptable quality?

**Measure:** MRR at each shots value (512, 1024, 2048, 4096).

**Result interpretation:** The shot noise model (1/√shots) is identical on simulator and
real hardware. This curve transfers directly — it gives the minimum shot budget under ideal
conditions. Real hardware would need more shots to compensate for physical noise, so our
curve is a lower bound.

**Engines:** `quantum_mock_sampler`, `qiskit_swap_test`

---

### Bonus: Scaling with dimension

Run each engine at dim=64 and dim=128 to measure:
- How MRR changes with dimension (does accuracy hold up?)
- How circuit depth grows (linear? worse?)
- How qubit count grows (log₂(dim) + 1 — verify theory matches practice)

---

## How to Read the Benchmark Report

`backend/docs/benchmark_report.md` maps directly to the thesis:

| Report section | Answers |
|---|---|
| Quality KPIs by Engine | Sub-question 1 (accuracy) |
| Head-to-Head Quality Comparison | Sub-question 1, per-query detail |
| Quantum Circuit Complexity | Sub-question 2 (resource cost) |
| Quantum: Shots vs. Quality | Sub-question 3 (measurement budget) |
| Quality by Dimension | Scaling analysis |
| Speed Scaling by Dimension | Intra-engine only |

---

## The Thesis Conclusion Template

1. **Accuracy:** `qiskit_swap_test` achieved MRR of X.XXX vs X.XXX for `brute_force_cosine`.
   The quantum algorithm [matches / falls short by N%] at [shot count] shots on AerSimulator.
   This includes shot noise but no physical hardware noise. Real hardware would score lower.

2. **Resource cost:** At 64-dim: 13 qubits, depth D. At 128-dim: 15 qubits, depth D'. Growth
   is [as expected / faster than expected].

3. **Shot budget:** MRR reaches acceptable threshold at N shots. Below that, ranking quality
   degrades significantly.

4. **Bottleneck:** State preparation costs O(n) gates — same as classical search. The quantum
   similarity computation is correct; the unsolved problem is efficient data loading (qRAM).

5. **Implication:** Quantum vector search is algorithmically correct but currently impractical
   at scale due to state preparation overhead and near-term hardware limitations. The
   benchmarking framework provides the baseline for re-evaluation as hardware improves.

6. **Trade-off framing:** This fits the accuracy-speed trade-off already understood in
   classical search (HNSW, IVF approximate indices sacrifice some accuracy for speed). Quantum
   search with qRAM would represent the same trade-off at a different scale: some accuracy
   cost from shot noise, in exchange for better asymptotic complexity on large datasets. The
   project quantifies the accuracy cost side of that trade-off.
