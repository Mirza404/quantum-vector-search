# Research Questions & Thesis Guide

What the thesis asks, what we benchmark, and how results lead to conclusions. For theory: [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md).

---

## The Thesis Question

> **On a mathematically exact quantum simulator, can the quantum swap test perform cross-modal vector similarity search with accuracy comparable to classical search, and what quantum resource cost does it require as a function of vector dimension?**

Two parts: **accuracy** and **cost**.

Everything runs on **AerSimulator** (Qiskit's noiseless simulator):
- Accuracy results are the **best-case ceiling** -- real hardware would score lower
- Circuit depth and qubit counts are **hardware-agnostic** -- properties of the circuit, not the platform

**What we're NOT asking:** Whether quantum is faster (it isn't) or whether it will beat classical (unknown, depends on qRAM).

**What we ARE asking:** Does the algorithm work under ideal conditions, and what does it cost?

<details><summary>Self-test</summary>

**Q: Why use a simulator instead of real hardware?**
A: AerSimulator is mathematically exact -- isolates shot noise from hardware noise. Gives the best-case accuracy ceiling.

**Q: If not claiming quantum is faster, what's the point?**
A: Establishing a baseline. When qRAM and better hardware arrive, we'll already know the algorithm works and what it costs.
</details>

---

## What Is Known vs. What This Project Contributes

| Known from theory | This project adds |
|---|---|
| Grover's gives O(sqrt(N)) search | **Empirical proof** the swap test works on AerSimulator |
| qRAM would unlock it for vector search | **Measured circuit depth and qubit counts** from compiled circuits |
| qRAM doesn't exist at practical scale | **Identified bottleneck:** state prep = O(n), same as classical |
| Swap test computes same result as cosine | **Benchmarking framework** ready for re-evaluation |

**What we do NOT claim:** quantum is faster, we found a new speedup, or wall-clock comparison is meaningful on a simulator.

> **Analogy:** Test-driving a prototype car on a treadmill. We can verify the engine works and measure fuel consumption, but can't compare lap times to a real car on a real track.

**In one sentence:** Theory says quantum search could be better with qRAM; this project proves the algorithm works and measures what it costs.

<details><summary>Self-test</summary>

**Q: What has this project proven beyond theory?**
A: Theory says the swap test should work. We verified it empirically with specific MRR numbers on CLIP embeddings and Flickr30k images.
</details>

---

## The Three Sub-Questions

### Sub-question 1: Does the quantum algorithm produce correct results?

**Metric:** MRR for each engine. **"Correct" =** `qiskit_swap_test` MRR close to `brute_force_cosine` MRR.

| Outcome | Interpretation |
|---|---|
| MRR matches | Swap test is correct at this shot count |
| MRR significantly lower | Shot noise is scrambling rankings -- need more shots |

The mock sampler is a **sanity check**: if it and Qiskit produce similar MRR, the noise model is valid.

**In one sentence:** Does the quantum engine find the right images, measured by comparing its MRR to classical ground truth?

<details><summary>Self-test</summary>

**Q: If Qiskit gets MRR 0.95 and brute-force gets 1.0?**
A: Quantum is mostly correct -- shot noise causes slight errors. More shots should close the gap.

**Q: Role of the mock sampler?**
A: Validates noise model. If mock and Qiskit give similar MRR, the noise is just shot noise. If Qiskit is worse, there's extra circuit overhead.
</details>

---

### Sub-question 2: What hardware resources does it need?

**Metrics:** Circuit depth and qubit count at each dimension.

| Metric | Why | Practical limit |
|---|---|---|
| **Circuit depth** | Deeper = more decoherence | NISQ: ~100 layers |
| **Qubit count** | More = harder to allocate | Current QPUs: 100-1000 |

Extracted from compiled Qiskit circuits: `circuit.depth()` and `circuit.num_qubits` in `_run_swap_test()`.

**Concrete claim:** "128-dim quantum search needs at least 15 qubits and coherence time for depth D."

<details><summary>Self-test</summary>

**Q: Why are circuit metrics "hardware-agnostic"?**
A: They describe circuit structure (gates, qubits), not how a specific chip runs it. Same circuit on any quantum computer.
</details>

---

### Sub-question 3: How many shots for acceptable quality?

**Metric:** MRR at each shots value (from `benchmarks.yaml`, `shots_values:`).

Shot noise (1/sqrt(shots)) is identical on simulator and real hardware. Our results are a **lower bound** -- real hardware needs more shots to compensate for physical noise.

**In one sentence:** How many measurements before results are reliable -- giving the minimum shot budget under ideal conditions.

<details><summary>Self-test</summary>

**Q: MRR acceptable at 1024 shots on simulator -- what about real hardware?**
A: At least 1024 (probably more due to physical noise). Our number is the floor.
</details>

---

### Bonus: Scaling with Dimension

Run at dim=64 and dim=128 to measure:
- MRR vs. dimension (does accuracy hold at lower dims?)
- Circuit depth vs. dimension (linear growth? worse?)
- Qubit count vs. dimension (should be log2(dim)+1 per register -- verify)

---

## Reading the Benchmark Report

`backend/docs/benchmark_report.md` (generated by `backend/scripts/generate_report.py`):

| Report section | Answers |
|---|---|
| Quality KPIs by Engine | Sub-Q 1 (accuracy) |
| Head-to-Head Comparison | Sub-Q 1 per-query detail |
| Quantum Circuit Complexity | Sub-Q 2 (resource cost) |
| Shots vs. Quality | Sub-Q 3 (measurement budget) |
| Quality by Dimension | Scaling analysis |
| Speed by Dimension | Intra-engine only (NOT cross-engine) |

---

## Thesis Conclusion Template

Fill in with your benchmark numbers:

1. **Accuracy:** `qiskit_swap_test` MRR = ___ vs `brute_force_cosine` MRR = ___. Quantum [matches / falls short by N%] at [shot count] shots. Includes shot noise, no hardware noise
2. **Resource cost:** 64-dim: 13 qubits, depth ___. 128-dim: 15 qubits, depth ___
3. **Shot budget:** MRR reaches acceptable threshold at ___ shots
4. **Bottleneck:** State preparation = O(n) gates, same as classical. Quantum similarity is correct; unsolved problem = efficient data loading (qRAM)
5. **Implication:** Algorithmically correct but currently impractical. Framework provides the baseline for re-evaluation

<details><summary>Self-test (defense prep)</summary>

**Q: "So quantum is useless for search?"**
A: "Not useless -- algorithmically correct but blocked by state preparation cost. The algorithm works on the simulator. What's missing is qRAM. Our framework is ready for when that changes."

**Q: "Why not test on real IBM hardware?"**
A: "Our circuits (13-15 qubits) fit the free tier. The valuable result would be the accuracy gap -- empirical evidence for why circuit depth matters."

**Q: Single most important number in the report?**
A: "MRR comparison between `qiskit_swap_test` and `brute_force_cosine`. If they match, the algorithm is correct. Everything else follows."
</details>
