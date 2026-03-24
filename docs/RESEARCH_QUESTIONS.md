# Research Questions & Thesis Guide

This document answers three things:
1. What is the thesis question?
2. What do we benchmark and why?
3. How do the results let us draw conclusions?

---

## The Thesis Question

> **Can the quantum swap test algorithm perform cross-modal vector similarity search with accuracy comparable to classical search, and what quantum resource cost does it require as a function of vector dimension?**

That is it. One question, two parts: **accuracy** and **cost**.

We are NOT asking whether quantum is faster. We cannot answer that — quantum runs on a
classical simulator here. Speed comparison would be meaningless.

We are NOT claiming quantum will ever beat classical search. We are asking whether the
quantum algorithm even produces correct results, and what it would cost on real hardware.

---

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
- If MRR matches → the quantum swap test algorithm is correct. Shot noise does not
  scramble rankings at our chosen shot count. The algorithm is viable in principle.
- If MRR is significantly lower → the shot noise is too high, or the circuit has a bug.
  We need more shots or there is a fundamental accuracy problem.

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

**What the result means for the thesis:** On real hardware every shot costs time and money.
The shots-vs-MRR curve shows the minimum measurement budget to reach a target accuracy.
Below some threshold, shot noise dominates and rankings are unreliable. Above the threshold,
the quantum engine converges to classical accuracy. This is a concrete operational parameter
for any real deployment.

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

1. **Accuracy:** The `qiskit_swap_test` engine achieved MRR of X.XXX, compared to
   X.XXX for `brute_force_cosine` (the exact classical baseline). The quantum algorithm
   [matches / falls short by N%] at [shot count] shots.

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
